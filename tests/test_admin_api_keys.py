"""Tests for admin API key management and REST auth integration."""

from __future__ import annotations

import hashlib
import json
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

    def count(self) -> int:
        return len(self.memories)

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

    def search(self, query: str = "", tags=None, agent=None, limit: int = 10):
        items = list(self.memories.values())
        if agent:
            items = [memory for memory in items if memory.agent == agent]
        if query:
            lowered = query.lower()
            items = [memory for memory in items if lowered in memory.content.lower()]
        return items[:limit]

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
        if "agent" in updates:
            memory.agent = updates["agent"]
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


def test_admin_agents_endpoint_lists_managed_agents_with_memory_counts(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("ADMIN_AUTH_CONFIG_PATH", str(tmp_path / "admin_auth.json"))
    monkeypatch.setenv("ADMIN_API_KEYS_PATH", str(tmp_path / "api_keys.json"))

    app = create_app(FakeWritableEngine(), auth_config={})
    client = TestClient(app)
    admin_headers = _login_admin(client)

    alice_key = client.post(
        "/admin/api/api-keys",
        headers=admin_headers,
        json={"name": "alice", "permissions": "read_write"},
    )
    bob_key = client.post(
        "/admin/api/api-keys",
        headers=admin_headers,
        json={"name": "bob", "permissions": "read"},
    )
    assert alice_key.status_code == 201
    assert bob_key.status_code == 201

    alice_headers = {"X-API-Key": alice_key.json()["full_key"]}
    for payload in (
        {"content": "Alice private 1"},
        {"content": "Alice private 2"},
    ):
        created = client.post("/api/v1/memories", headers=alice_headers, json=payload)
        assert created.status_code == 201

    agents_response = client.get("/admin/api/agents", headers=admin_headers)

    assert agents_response.status_code == 200
    agents = {item["agent_id"]: item for item in agents_response.json()}
    assert agents["alice"]["name"] == "alice"
    assert agents["alice"]["permissions"] == "read_write"
    assert agents["alice"]["memory_count"] == 2
    assert agents["alice"]["api_key_preview"] == alice_key.json()["key_preview"]
    assert agents["alice"]["last_active"] is not None
    assert agents["bob"]["permissions"] == "read"
    assert agents["bob"]["memory_count"] == 0
    assert agents["bob"]["api_key_preview"] == bob_key.json()["key_preview"]



def test_admin_agents_endpoint_includes_acl_only_agents_without_api_keys(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("ADMIN_AUTH_CONFIG_PATH", str(tmp_path / "admin_auth.json"))
    monkeypatch.setenv("ADMIN_API_KEYS_PATH", str(tmp_path / "api_keys.json"))

    auth_config = {
        "acl": {
            "agents": {
                "planner": {
                    "name": "Planner Agent",
                    "permissions": {
                        "namespace": "planner:*",
                        "operations": ["read", "write"],
                    },
                },
                "observer": {
                    "permissions": {
                        "namespace": "observer:*",
                        "operations": ["read"],
                    },
                },
                "default": {
                    "permissions": {
                        "namespace": "${agent_id}:*",
                        "operations": ["read"],
                    },
                },
            }
        }
    }

    app = create_app(FakeWritableEngine(), auth_config=auth_config)
    client = TestClient(app)
    admin_headers = _login_admin(client)

    agents_response = client.get("/admin/api/agents", headers=admin_headers)

    assert agents_response.status_code == 200
    agents = {item["agent_id"]: item for item in agents_response.json()}
    assert agents["planner"] == {
        "agent_id": "planner",
        "name": "Planner Agent",
        "permissions": "read_write",
        "last_active": None,
        "memory_count": 0,
        "api_key_preview": "-",
    }
    assert agents["observer"] == {
        "agent_id": "observer",
        "name": None,
        "permissions": "read",
        "last_active": None,
        "memory_count": 0,
        "api_key_preview": "-",
    }
    assert "default" not in agents


def test_admin_agents_endpoint_prefers_newest_key_when_agent_has_multiple_keys(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("ADMIN_AUTH_CONFIG_PATH", str(tmp_path / "admin_auth.json"))
    monkeypatch.setenv("ADMIN_API_KEYS_PATH", str(tmp_path / "api_keys.json"))

    app = create_app(FakeWritableEngine(), auth_config={})
    client = TestClient(app)
    admin_headers = _login_admin(client)

    older_key = client.post(
        "/admin/api/api-keys",
        headers=admin_headers,
        json={"name": "planner-read", "permissions": "read", "agent_id": "planner"},
    )
    newer_key = client.post(
        "/admin/api/api-keys",
        headers=admin_headers,
        json={"name": "planner-write", "permissions": "read_write", "agent_id": "planner"},
    )
    assert older_key.status_code == 201
    assert newer_key.status_code == 201

    planner_headers = {"X-API-Key": newer_key.json()["full_key"]}
    created = client.post(
        "/api/v1/memories",
        headers=planner_headers,
        json={"content": "Planner memory"},
    )
    assert created.status_code == 201

    agents_response = client.get("/admin/api/agents", headers=admin_headers)

    assert agents_response.status_code == 200
    agents = {item["agent_id"]: item for item in agents_response.json()}
    assert agents["planner"]["name"] == "planner-write"
    assert agents["planner"]["permissions"] == "read_write"
    assert agents["planner"]["api_key_preview"] == newer_key.json()["key_preview"]
    assert agents["planner"]["last_active"] is not None
    assert agents["planner"]["memory_count"] == 1


def test_managed_api_keys_default_to_agent_identity_and_scope_memory_access(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("ADMIN_AUTH_CONFIG_PATH", str(tmp_path / "admin_auth.json"))
    monkeypatch.setenv("ADMIN_API_KEYS_PATH", str(tmp_path / "api_keys.json"))

    app = create_app(FakeWritableEngine(), auth_config={})
    client = TestClient(app)
    admin_headers = _login_admin(client)

    alice_key = client.post(
        "/admin/api/api-keys",
        headers=admin_headers,
        json={"name": "alice", "permissions": "read_write"},
    )
    assert alice_key.status_code == 201
    assert alice_key.json()["agent_id"] == "alice"

    bob_key = client.post(
        "/admin/api/api-keys",
        headers=admin_headers,
        json={"name": "bob", "permissions": "read_write"},
    )
    assert bob_key.status_code == 201
    assert bob_key.json()["agent_id"] == "bob"

    alice_headers = {"X-API-Key": alice_key.json()["full_key"]}
    bob_headers = {"X-API-Key": bob_key.json()["full_key"]}

    created = client.post(
        "/api/v1/memories",
        headers=alice_headers,
        json={"content": "Alice private note"},
    )
    assert created.status_code == 201
    memory_id = created.json()["id"]
    assert created.json()["agent"] == "alice"

    alice_list = client.get("/api/v1/memories", headers=alice_headers)
    assert alice_list.status_code == 200
    assert [item["id"] for item in alice_list.json()["memories"]] == [memory_id]

    bob_list = client.get("/api/v1/memories", headers=bob_headers)
    assert bob_list.status_code == 200
    assert bob_list.json()["memories"] == []

    bob_get = client.get(f"/api/v1/memories/{memory_id}", headers=bob_headers)
    assert bob_get.status_code == 403

    bob_delete = client.delete(f"/api/v1/memories/{memory_id}", headers=bob_headers)
    assert bob_delete.status_code == 403


def test_agent_bound_key_cannot_create_memory_for_another_agent(tmp_path, monkeypatch) -> None:
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

    response = client.post(
        "/api/v1/memories",
        headers={"X-API-Key": full_key},
        json={"content": "blocked", "agent": "other-agent"},
    )

    assert response.status_code == 403


def test_agent_bound_key_cannot_update_or_query_another_agent_namespace(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("ADMIN_AUTH_CONFIG_PATH", str(tmp_path / "admin_auth.json"))
    monkeypatch.setenv("ADMIN_API_KEYS_PATH", str(tmp_path / "api_keys.json"))

    app = create_app(FakeWritableEngine(), auth_config={})
    client = TestClient(app)
    admin_headers = _login_admin(client)

    alice_key = client.post(
        "/admin/api/api-keys",
        headers=admin_headers,
        json={"name": "alice", "permissions": "read_write"},
    )
    bob_key = client.post(
        "/admin/api/api-keys",
        headers=admin_headers,
        json={"name": "bob", "permissions": "read_write"},
    )
    assert alice_key.status_code == 201
    assert bob_key.status_code == 201

    alice_headers = {"X-API-Key": alice_key.json()["full_key"]}
    bob_headers = {"X-API-Key": bob_key.json()["full_key"]}

    created = client.post(
        "/api/v1/memories",
        headers=alice_headers,
        json={"content": "Alice private note"},
    )
    assert created.status_code == 201
    memory_id = created.json()["id"]

    forbidden_update = client.put(
        f"/api/v1/memories/{memory_id}",
        headers=bob_headers,
        json={"content": "Bob should not edit this"},
    )
    assert forbidden_update.status_code == 403

    forbidden_query = client.get("/api/v1/memories?agent=alice", headers=bob_headers)
    assert forbidden_query.status_code == 403


def test_managed_admin_key_can_access_memories_across_agents(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("ADMIN_AUTH_CONFIG_PATH", str(tmp_path / "admin_auth.json"))
    monkeypatch.setenv("ADMIN_API_KEYS_PATH", str(tmp_path / "api_keys.json"))

    app = create_app(FakeWritableEngine(), auth_config={})
    client = TestClient(app)
    admin_headers = _login_admin(client)

    alice_key = client.post(
        "/admin/api/api-keys",
        headers=admin_headers,
        json={"name": "alice", "permissions": "read_write"},
    )
    admin_key = client.post(
        "/admin/api/api-keys",
        headers=admin_headers,
        json={"name": "ops-admin", "permissions": "admin"},
    )
    assert alice_key.status_code == 201
    assert admin_key.status_code == 201

    alice_headers = {"X-API-Key": alice_key.json()["full_key"]}
    managed_admin_headers = {"X-API-Key": admin_key.json()["full_key"]}

    created = client.post(
        "/api/v1/memories",
        headers=alice_headers,
        json={"content": "Alice private note"},
    )
    assert created.status_code == 201
    memory_id = created.json()["id"]

    get_response = client.get(f"/api/v1/memories/{memory_id}", headers=managed_admin_headers)
    assert get_response.status_code == 200
    assert get_response.json()["agent"] == "alice"

    delete_response = client.delete(f"/api/v1/memories/{memory_id}", headers=managed_admin_headers)
    assert delete_response.status_code == 200


def test_agent_bound_keys_can_read_shared_namespace_but_not_write_it(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("ADMIN_AUTH_CONFIG_PATH", str(tmp_path / "admin_auth.json"))
    monkeypatch.setenv("ADMIN_API_KEYS_PATH", str(tmp_path / "api_keys.json"))

    app = create_app(FakeWritableEngine(), auth_config={})
    client = TestClient(app)
    admin_headers = _login_admin(client)

    alice_key = client.post(
        "/admin/api/api-keys",
        headers=admin_headers,
        json={"name": "alice", "permissions": "read_write"},
    )
    bob_key = client.post(
        "/admin/api/api-keys",
        headers=admin_headers,
        json={"name": "bob", "permissions": "read_write"},
    )
    admin_key = client.post(
        "/admin/api/api-keys",
        headers=admin_headers,
        json={"name": "ops-admin", "permissions": "admin"},
    )
    assert alice_key.status_code == 201
    assert bob_key.status_code == 201
    assert admin_key.status_code == 201

    alice_headers = {"X-API-Key": alice_key.json()["full_key"]}
    bob_headers = {"X-API-Key": bob_key.json()["full_key"]}
    managed_admin_headers = {"X-API-Key": admin_key.json()["full_key"]}

    alice_private = client.post(
        "/api/v1/memories",
        headers=alice_headers,
        json={"content": "Alice private note"},
    )
    assert alice_private.status_code == 201

    shared_memory = client.post(
        "/api/v1/memories",
        headers=managed_admin_headers,
        json={"content": "Shared runbook", "agent": "shared", "tags": ["shared"]},
    )
    assert shared_memory.status_code == 201
    shared_id = shared_memory.json()["id"]

    alice_list = client.get("/api/v1/memories", headers=alice_headers)
    assert alice_list.status_code == 200
    assert {item["agent"] for item in alice_list.json()["memories"]} == {"alice", "shared"}

    bob_list = client.get("/api/v1/memories", headers=bob_headers)
    assert bob_list.status_code == 200
    assert [item["id"] for item in bob_list.json()["memories"]] == [shared_id]

    shared_query = client.get("/api/v1/memories?agent=shared", headers=alice_headers)
    assert shared_query.status_code == 200
    assert [item["id"] for item in shared_query.json()["memories"]] == [shared_id]

    shared_get = client.get(f"/api/v1/memories/{shared_id}", headers=bob_headers)
    assert shared_get.status_code == 200
    assert shared_get.json()["agent"] == "shared"

    forbidden_create = client.post(
        "/api/v1/memories",
        headers=alice_headers,
        json={"content": "Should fail", "agent": "shared"},
    )
    assert forbidden_create.status_code == 403

    forbidden_update = client.put(
        f"/api/v1/memories/{shared_id}",
        headers=alice_headers,
        json={"content": "Should fail"},
    )
    assert forbidden_update.status_code == 403

    forbidden_delete = client.delete(f"/api/v1/memories/{shared_id}", headers=bob_headers)
    assert forbidden_delete.status_code == 403


def test_non_admin_api_keys_cannot_bind_to_reserved_shared_agent(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("ADMIN_AUTH_CONFIG_PATH", str(tmp_path / "admin_auth.json"))
    monkeypatch.setenv("ADMIN_API_KEYS_PATH", str(tmp_path / "api_keys.json"))

    app = create_app(FakeWritableEngine(), auth_config={})
    client = TestClient(app)
    admin_headers = _login_admin(client)

    explicit_shared = client.post(
        "/admin/api/api-keys",
        headers=admin_headers,
        json={"name": "shared-writer", "permissions": "read_write", "agent_id": "shared"},
    )
    assert explicit_shared.status_code == 400

    implicit_shared = client.post(
        "/admin/api/api-keys",
        headers=admin_headers,
        json={"name": "shared", "permissions": "read_write"},
    )
    assert implicit_shared.status_code == 400

    admin_shared = client.post(
        "/admin/api/api-keys",
        headers=admin_headers,
        json={"name": "shared-admin", "permissions": "admin", "agent_id": "shared"},
    )
    assert admin_shared.status_code == 201


def test_non_admin_search_filters_before_limiting_visible_results(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("ADMIN_AUTH_CONFIG_PATH", str(tmp_path / "admin_auth.json"))
    monkeypatch.setenv("ADMIN_API_KEYS_PATH", str(tmp_path / "api_keys.json"))

    app = create_app(FakeWritableEngine(), auth_config={})
    client = TestClient(app)
    admin_headers = _login_admin(client)

    alice_key = client.post(
        "/admin/api/api-keys",
        headers=admin_headers,
        json={"name": "alice", "permissions": "read_write"},
    )
    admin_key = client.post(
        "/admin/api/api-keys",
        headers=admin_headers,
        json={"name": "ops-admin", "permissions": "admin"},
    )
    assert alice_key.status_code == 201
    assert admin_key.status_code == 201

    alice_headers = {"X-API-Key": alice_key.json()["full_key"]}
    managed_admin_headers = {"X-API-Key": admin_key.json()["full_key"]}

    for payload in (
        {"content": "match bob one", "agent": "bob"},
        {"content": "match bob two", "agent": "bob"},
        {"content": "match alice private", "agent": "alice"},
        {"content": "match shared note", "agent": "shared"},
    ):
        created = client.post("/api/v1/memories", headers=managed_admin_headers, json=payload)
        assert created.status_code == 201

    response = client.get("/api/v1/memories?q=match&limit=2", headers=alice_headers)
    assert response.status_code == 200
    assert [item["agent"] for item in response.json()["memories"]] == ["alice", "shared"]
    assert response.json()["total"] == 2


def test_managed_key_can_override_display_name_with_explicit_agent_id(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("ADMIN_AUTH_CONFIG_PATH", str(tmp_path / "admin_auth.json"))
    monkeypatch.setenv("ADMIN_API_KEYS_PATH", str(tmp_path / "api_keys.json"))

    app = create_app(FakeWritableEngine(), auth_config={})
    client = TestClient(app)
    admin_headers = _login_admin(client)

    created = client.post(
        "/admin/api/api-keys",
        headers=admin_headers,
        json={"name": "worker-key", "permissions": "read_write", "agent_id": "planner"},
    )
    assert created.status_code == 201
    assert created.json()["agent_id"] == "planner"

    response = client.post(
        "/api/v1/memories",
        headers={"X-API-Key": created.json()["full_key"]},
        json={"content": "Planning note"},
    )
    assert response.status_code == 201
    assert response.json()["agent"] == "planner"


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


def test_api_key_store_default_path_uses_cwd_data_dir(monkeypatch, tmp_path) -> None:
    monkeypatch.delenv("ADMIN_API_KEYS_PATH", raising=False)
    monkeypatch.chdir(tmp_path)

    app = create_app(FakeEngine(), auth_config={})
    store = app.state.api_key_store

    assert store.path.is_absolute() is True
    assert store.path == tmp_path / "data" / "api_keys.json"


def test_legacy_managed_key_without_agent_id_keeps_unscoped_behavior(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("ADMIN_AUTH_CONFIG_PATH", str(tmp_path / "admin_auth.json"))
    legacy_store_path = tmp_path / "api_keys.json"
    monkeypatch.setenv("ADMIN_API_KEYS_PATH", str(legacy_store_path))

    legacy_key = "amk_legacy_reader"
    legacy_store_path.write_text(
        json.dumps(
            {
                "enforced": True,
                "api_keys": [
                    {
                        "key_preview": "amk_legacy_r...",
                        "name": "legacy-reader",
                        "permissions": "read_write",
                        "description": "pre-agent-id key",
                        "created_at": "2026-05-01T00:00:00",
                        "last_used": None,
                        "usage_count": 0,
                        "key_hash": hashlib.sha256(legacy_key.encode("utf-8")).hexdigest(),
                    }
                ],
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )

    app = create_app(FakeWritableEngine(), auth_config={})
    client = TestClient(app)
    admin_headers = _login_admin(client)

    admin_key = client.post(
        "/admin/api/api-keys",
        headers=admin_headers,
        json={"name": "ops-admin", "permissions": "admin"},
    )
    assert admin_key.status_code == 201
    managed_admin_headers = {"X-API-Key": admin_key.json()["full_key"]}

    bob_memory = client.post(
        "/api/v1/memories",
        headers=managed_admin_headers,
        json={"content": "Bob memory", "agent": "bob"},
    )
    assert bob_memory.status_code == 201

    legacy_headers = {"X-API-Key": legacy_key}
    listing = client.get("/api/v1/memories?agent=bob", headers=legacy_headers)
    assert listing.status_code == 200
    assert listing.json()["memories"][0]["agent"] == "bob"

    api_keys = client.get("/admin/api/api-keys", headers=admin_headers)
    assert api_keys.status_code == 200
    legacy_record = next(item for item in api_keys.json() if item["name"] == "legacy-reader")
    assert legacy_record["agent_id"] is None



def test_acl_can_disable_shared_reads_for_managed_non_admin_keys(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("ADMIN_AUTH_CONFIG_PATH", str(tmp_path / "admin_auth.json"))
    monkeypatch.setenv("ADMIN_API_KEYS_PATH", str(tmp_path / "api_keys.json"))

    acl_config = {
        "agents": {
            "claude-code": {
                "permissions": {
                    "namespace": "claude-code:*",
                    "operations": ["read", "write"],
                }
            }
        }
    }

    app = create_app(FakeWritableEngine(), auth_config={"acl": acl_config})
    client = TestClient(app)
    admin_headers = _login_admin(client)

    claude_key = client.post(
        "/admin/api/api-keys",
        headers=admin_headers,
        json={"name": "claude-worker", "permissions": "read_write", "agent_id": "claude-code"},
    )
    admin_key = client.post(
        "/admin/api/api-keys",
        headers=admin_headers,
        json={"name": "ops-admin", "permissions": "admin"},
    )
    assert claude_key.status_code == 201
    assert admin_key.status_code == 201

    claude_headers = {"X-API-Key": claude_key.json()["full_key"]}
    managed_admin_headers = {"X-API-Key": admin_key.json()["full_key"]}

    private_memory = client.post(
        "/api/v1/memories",
        headers=claude_headers,
        json={"content": "Claude private note"},
    )
    assert private_memory.status_code == 201

    shared_memory = client.post(
        "/api/v1/memories",
        headers=managed_admin_headers,
        json={"content": "Shared runbook", "agent": "shared"},
    )
    assert shared_memory.status_code == 201
    shared_id = shared_memory.json()["id"]

    listing = client.get("/api/v1/memories", headers=claude_headers)
    assert listing.status_code == 200
    assert [item["agent"] for item in listing.json()["memories"]] == ["claude-code"]

    shared_query = client.get("/api/v1/memories?agent=shared", headers=claude_headers)
    assert shared_query.status_code == 403

    shared_get = client.get(f"/api/v1/memories/{shared_id}", headers=claude_headers)
    assert shared_get.status_code == 403



def test_acl_delete_operation_can_block_non_admin_deletes_in_own_namespace(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("ADMIN_AUTH_CONFIG_PATH", str(tmp_path / "admin_auth.json"))
    monkeypatch.setenv("ADMIN_API_KEYS_PATH", str(tmp_path / "api_keys.json"))

    acl_config = {
        "agents": {
            "claude-code": {
                "permissions": {
                    "namespace": "claude-code:*",
                    "operations": ["read", "write"],
                }
            }
        }
    }

    app = create_app(FakeWritableEngine(), auth_config={"acl": acl_config})
    client = TestClient(app)
    admin_headers = _login_admin(client)

    claude_key = client.post(
        "/admin/api/api-keys",
        headers=admin_headers,
        json={"name": "claude-worker", "permissions": "read_write", "agent_id": "claude-code"},
    )
    assert claude_key.status_code == 201
    claude_headers = {"X-API-Key": claude_key.json()["full_key"]}

    created = client.post(
        "/api/v1/memories",
        headers=claude_headers,
        json={"content": "Keep me"},
    )
    assert created.status_code == 201

    deleted = client.delete(f"/api/v1/memories/{created.json()['id']}", headers=claude_headers)
    assert deleted.status_code == 403
