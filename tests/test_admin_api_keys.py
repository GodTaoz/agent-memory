"""Tests for admin API key management and REST auth integration."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from fastapi.testclient import TestClient

from memory_mcp.models import Memory
from memory_mcp.protocol.rest import create_app


class FakeEngine:
    def count(self) -> int:
        return 0

    def list_memories(self, limit: int = 10, offset: int = 0):
        return []

    def search(self, query: str = "", tags=None, agent=None, limit: int = 10):
        return []

    def get(self, memory_id: str):
        return None

    def update(self, memory_id: str, updates: dict):
        return None

    def delete(self, memory_id: str) -> bool:
        return False


class FakeWritableEngine(FakeEngine):
    def __init__(self) -> None:
        self.memories: dict[str, Memory] = {}
        self.counter = 0

    def generate_id(self) -> str:
        self.counter += 1
        return f"mem_{self.counter}"

    def save(self, memory: Memory) -> bool:
        now = datetime.now(timezone.utc)
        memory.created_at = now
        memory.updated_at = now
        self.memories[memory.id] = memory
        return True

    def list_memories(self, limit: int = 10, offset: int = 0):
        items = list(self.memories.values())
        return items[offset : offset + limit]

    def get(self, memory_id: str) -> Optional[Memory]:
        return self.memories.get(memory_id)

    def update(self, memory_id: str, updates: dict):
        memory = self.memories.get(memory_id)
        if memory is None:
            return None
        if "content" in updates:
            memory.content = updates["content"]
        if "tags" in updates:
            memory.tags = updates["tags"]
        memory.updated_at = datetime.now(timezone.utc)
        memory.version += 1
        return memory

    def delete(self, memory_id: str) -> bool:
        return self.memories.pop(memory_id, None) is not None


def _login_admin(client: TestClient) -> dict[str, str]:
    response = client.post("/admin/api/auth/login", json={"password": "admin123"})
    assert response.status_code == 200
    token = response.json()["token"]
    return {"Authorization": f"Bearer {token}"}


def test_admin_can_create_list_and_delete_api_key(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("ADMIN_API_KEYS_PATH", str(tmp_path / "api_keys.json"))
    monkeypatch.setenv("ADMIN_AUTH_CONFIG_PATH", str(tmp_path / "admin_auth.json"))

    app = create_app(FakeEngine(), auth_config={})
    client = TestClient(app)
    admin_headers = _login_admin(client)

    create_response = client.post(
        "/admin/api/api-keys",
        headers=admin_headers,
        json={
            "name": "integration-agent",
            "permissions": "read_write",
            "description": "Used by the integration test agent.",
        },
    )
    assert create_response.status_code == 201
    created = create_response.json()
    assert created["name"] == "integration-agent"
    assert created["permissions"] == "read_write"
    assert created["full_key"].startswith("amk_")
    assert created["key_preview"].endswith("...")
    assert created["usage_count"] == 0
    assert created["last_used"] is None

    list_response = client.get("/admin/api/api-keys", headers=admin_headers)
    assert list_response.status_code == 200
    payload = list_response.json()
    assert len(payload) == 1
    assert payload[0]["name"] == "integration-agent"
    assert payload[0]["key_preview"] == created["key_preview"]

    delete_response = client.delete(f"/admin/api/api-keys/{created['key_preview']}", headers=admin_headers)
    assert delete_response.status_code == 200
    assert delete_response.json() == {"success": True}

    list_after_delete = client.get("/admin/api/api-keys", headers=admin_headers)
    assert list_after_delete.status_code == 200
    assert list_after_delete.json() == []


def test_created_api_key_grants_access_and_updates_usage_stats(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("ADMIN_AUTH_CONFIG_PATH", str(tmp_path / "admin_auth.json"))
    monkeypatch.setenv("ADMIN_API_KEYS_PATH", str(tmp_path / "api_keys.json"))

    app = create_app(FakeWritableEngine(), auth_config={})
    client = TestClient(app)
    admin_headers = _login_admin(client)

    created = client.post(
        "/admin/api/api-keys",
        headers=admin_headers,
        json={"name": "writer", "permissions": "read_write"},
    )
    assert created.status_code == 201
    full_key = created.json()["full_key"]

    response = client.get("/api/v1/memories", headers={"X-API-Key": full_key})
    assert response.status_code == 200

    listing = client.get("/admin/api/api-keys", headers=admin_headers)
    payload = listing.json()
    assert payload[0]["usage_count"] == 1
    assert payload[0]["last_used"] is not None


def test_read_only_api_key_cannot_mutate_memories(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("ADMIN_AUTH_CONFIG_PATH", str(tmp_path / "admin_auth.json"))
    monkeypatch.setenv("ADMIN_API_KEYS_PATH", str(tmp_path / "api_keys.json"))

    app = create_app(FakeWritableEngine(), auth_config={})
    client = TestClient(app)
    admin_headers = _login_admin(client)

    created = client.post(
        "/admin/api/api-keys",
        headers=admin_headers,
        json={"name": "reader", "permissions": "read"},
    )
    assert created.status_code == 201
    full_key = created.json()["full_key"]

    write_response = client.post(
        "/api/v1/memories",
        headers={"X-API-Key": full_key},
        json={"content": "blocked", "tags": ["read-only"]},
    )

    assert write_response.status_code == 403


def test_deleted_api_key_is_revoked_immediately(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("ADMIN_API_KEYS_PATH", str(tmp_path / "api_keys.json"))
    monkeypatch.setenv("ADMIN_AUTH_CONFIG_PATH", str(tmp_path / "admin_auth.json"))

    app = create_app(FakeEngine(), auth_config={})
    client = TestClient(app)
    admin_headers = _login_admin(client)

    create_response = client.post(
        "/admin/api/api-keys",
        headers=admin_headers,
        json={"name": "reader", "permissions": "read", "description": None},
    )
    assert create_response.status_code == 201
    full_key = create_response.json()["full_key"]
    preview = create_response.json()["key_preview"]

    delete_response = client.delete(f"/admin/api/api-keys/{preview}", headers=admin_headers)
    assert delete_response.status_code == 200

    protected_response = client.get("/api/v1/memories", headers={"Authorization": f"Bearer {full_key}"})
    assert protected_response.status_code == 401


def test_api_key_store_file_permissions_are_owner_only(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("ADMIN_API_KEYS_PATH", str(tmp_path / "api_keys.json"))
    monkeypatch.setenv("ADMIN_AUTH_CONFIG_PATH", str(tmp_path / "admin_auth.json"))

    app = create_app(FakeEngine(), auth_config={})
    client = TestClient(app)
    admin_headers = _login_admin(client)

    create_response = client.post(
        "/admin/api/api-keys",
        headers=admin_headers,
        json={"name": "secure-reader", "permissions": "read"},
    )
    assert create_response.status_code == 201

    mode = Path(tmp_path / "api_keys.json").stat().st_mode & 0o777
    assert mode == 0o600
