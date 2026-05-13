"""Tests for admin memory management routes."""

from __future__ import annotations

from dataclasses import replace
from typing import List

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from memory_mcp.admin.auth import AdminAuth
from memory_mcp.admin.deps import get_admin_auth
from memory_mcp.admin.routes import router
from memory_mcp.models import Memory


class FakeAdminMemoryEngine:
    """Simple in-memory engine for admin route tests."""

    def __init__(self, memories: List[Memory]):
        self.memories = {memory.id: memory for memory in memories}

    def count(self) -> int:
        return len(self.memories)

    def list_memories(self, limit: int = 100, offset: int = 0):
        memories = sorted(self.memories.values(), key=lambda memory: memory.updated_at, reverse=True)
        return memories[offset : offset + limit]

    def search(self, query: str | None = None, tags: list[str] | None = None, agent: str | None = None, limit: int = 10):
        results = sorted(self.memories.values(), key=lambda memory: memory.updated_at, reverse=True)
        if query:
            results = [memory for memory in results if query.lower() in memory.content.lower()]
        if tags:
            wanted = set(tags)
            results = [memory for memory in results if wanted.intersection(memory.tags)]
        if agent:
            results = [memory for memory in results if memory.agent == agent]
        return results[:limit]

    def get(self, memory_id: str):
        return self.memories.get(memory_id)

    def update(self, memory_id: str, updates: dict):
        memory = self.memories.get(memory_id)
        if memory is None:
            return None

        if "content" in updates:
            memory.content = updates["content"]
        if "tags" in updates:
            memory.tags = updates["tags"]
        memory.version += 1
        self.memories[memory_id] = memory
        return memory

    def delete(self, memory_id: str) -> bool:
        return self.memories.pop(memory_id, None) is not None


@pytest.fixture
def admin_auth() -> AdminAuth:
    return AdminAuth()


@pytest.fixture
def memory_engine() -> FakeAdminMemoryEngine:
    memories = [
        Memory(id="mem_001", content="Owner prefers concise Python code.", tags=["coding", "preference"], agent="hermes"),
        Memory(id="mem_002", content="Deploy Redis on the NAS for shared memory.", tags=["infra", "nas"], agent="codex"),
        Memory(id="mem_003", content="Track weekly progress in the project journal.", tags=["planning"], agent="hermes"),
    ]
    return FakeAdminMemoryEngine(memories)


@pytest.fixture
def client(admin_auth: AdminAuth, memory_engine: FakeAdminMemoryEngine) -> TestClient:
    from memory_mcp.admin.deps import get_memory_engine

    app = FastAPI()
    app.include_router(router)
    app.dependency_overrides[get_admin_auth] = lambda: admin_auth
    app.dependency_overrides[get_memory_engine] = lambda: memory_engine
    return TestClient(app)


@pytest.fixture
def auth_headers(admin_auth: AdminAuth) -> dict[str, str]:
    token = admin_auth.create_session("admin123")
    return {"Authorization": f"Bearer {token}"}


def test_list_memories_returns_paginated_payload(client: TestClient, auth_headers: dict[str, str]) -> None:
    response = client.get("/admin/api/memories?page=1&page_size=2", headers=auth_headers)

    assert response.status_code == 200
    payload = response.json()
    assert payload["total"] == 3
    assert len(payload["memories"]) == 2
    assert payload["memories"][0]["key"] == "mem_003"


def test_list_memories_filters_by_search_query(client: TestClient, auth_headers: dict[str, str]) -> None:
    response = client.get("/admin/api/memories?search=Redis", headers=auth_headers)

    assert response.status_code == 200
    payload = response.json()
    assert payload["total"] == 1
    assert [memory["key"] for memory in payload["memories"]] == ["mem_002"]


def test_list_memories_filters_by_tag(client: TestClient, auth_headers: dict[str, str]) -> None:
    response = client.get("/admin/api/memories?tag=planning", headers=auth_headers)

    assert response.status_code == 200
    payload = response.json()
    assert payload["total"] == 1
    assert payload["memories"][0]["key"] == "mem_003"


def test_get_memory_returns_specific_memory(client: TestClient, auth_headers: dict[str, str]) -> None:
    response = client.get("/admin/api/memories/mem_001", headers=auth_headers)

    assert response.status_code == 200
    payload = response.json()
    assert payload["key"] == "mem_001"
    assert payload["agent_id"] == "hermes"


def test_update_memory_persists_changes(client: TestClient, auth_headers: dict[str, str]) -> None:
    response = client.put(
        "/admin/api/memories/mem_001",
        headers=auth_headers,
        json={"content": "Owner prefers elegant Python code.", "tags": ["coding", "style"]},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["content"] == "Owner prefers elegant Python code."
    assert payload["tags"] == ["coding", "style"]

    reread = client.get("/admin/api/memories/mem_001", headers=auth_headers)
    assert reread.status_code == 200
    assert reread.json()["content"] == "Owner prefers elegant Python code."


def test_delete_memory_removes_memory(client: TestClient, auth_headers: dict[str, str]) -> None:
    response = client.delete("/admin/api/memories/mem_002", headers=auth_headers)

    assert response.status_code == 200
    assert response.json() == {"success": True}

    reread = client.get("/admin/api/memories/mem_002", headers=auth_headers)
    assert reread.status_code == 404


def test_export_memories_json_uses_real_data(client: TestClient, auth_headers: dict[str, str]) -> None:
    response = client.get("/admin/api/memories/export/json?tag=planning", headers=auth_headers)

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("application/json")
    assert '"key": "mem_003"' in response.text
    assert '"content": "Track weekly progress in the project journal."' in response.text


def test_export_memories_csv_uses_real_data(client: TestClient, auth_headers: dict[str, str]) -> None:
    response = client.get("/admin/api/memories/export/csv?tag=coding", headers=auth_headers)

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/csv")
    assert "mem_001" in response.text
    assert "Owner prefers concise Python code." in response.text
