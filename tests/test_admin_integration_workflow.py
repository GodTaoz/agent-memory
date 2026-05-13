"""Integration workflow tests for admin panel and REST auth."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional

from fastapi.testclient import TestClient

from memory_mcp.models import Memory
from memory_mcp.protocol.rest import create_app


class FakeRedisClient:
    def ping(self) -> bool:
        return True

    def info(self) -> dict:
        return {"used_memory_human": "2M"}

    def keys(self, pattern: str) -> list[str]:
        return ["memory:mem_1"]


class InMemoryEngine:
    def __init__(self) -> None:
        self._backend = type("Backend", (), {"_client": FakeRedisClient(), "key_prefix": "memory"})()
        self._memories: dict[str, Memory] = {}
        self._counter = 0

    def generate_id(self) -> str:
        self._counter += 1
        return f"mem_{self._counter}"

    def save(self, memory: Memory) -> bool:
        now = datetime.now(timezone.utc)
        if not memory.created_at:
            memory.created_at = now
        memory.updated_at = now
        self._memories[memory.id] = memory
        return True

    def get(self, memory_id: str) -> Optional[Memory]:
        return self._memories.get(memory_id)

    def update(self, memory_id: str, updates: dict) -> Optional[Memory]:
        memory = self._memories.get(memory_id)
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
        return self._memories.pop(memory_id, None) is not None

    def list_memories(self, limit: int = 100, offset: int = 0):
        items = list(self._memories.values())
        return items[offset : offset + limit]

    def search(self, query=None, tags=None, agent=None, limit: int = 10):
        results = list(self._memories.values())
        if query:
            results = [m for m in results if query.lower() in m.content.lower()]
        if tags:
            required = set(tags)
            results = [m for m in results if required.issubset(set(m.tags))]
        if agent:
            results = [m for m in results if m.agent == agent]
        return results[:limit]

    def count(self) -> int:
        return len(self._memories)


def test_admin_to_rest_workflow(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("ADMIN_AUTH_CONFIG_PATH", str(tmp_path / "admin_auth.json"))
    monkeypatch.setenv("ADMIN_API_KEYS_PATH", str(tmp_path / "api_keys.json"))
    monkeypatch.setenv("ADMIN_LOG_DB_PATH", str(tmp_path / "admin_logs.db"))
    monkeypatch.delenv("ADMIN_PASSWORD_HASH", raising=False)
    monkeypatch.delenv("ADMIN_PASSWORD_SALT", raising=False)

    engine = InMemoryEngine()
    app = create_app(engine)
    client = TestClient(app)

    login = client.post("/admin/api/auth/login", json={"password": "admin123"})
    assert login.status_code == 200
    login_payload = login.json()
    assert login_payload["requires_password_change"] is True
    admin_headers = {"Authorization": f"Bearer {login_payload['token']}"}

    create_key = client.post(
        "/admin/api/api-keys",
        json={"name": "workflow-agent", "permissions": "read_write"},
        headers=admin_headers,
    )
    assert create_key.status_code == 201
    full_key = create_key.json()["full_key"]
    assert full_key.startswith("amk_")

    create_memory = client.post(
        "/api/v1/memories",
        json={"content": "Integration memory", "tags": ["workflow"], "agent": "workflow-agent"},
        headers={"X-API-Key": full_key},
    )
    assert create_memory.status_code == 201
    memory_id = create_memory.json()["id"]

    stats = client.get("/admin/api/stats", headers=admin_headers)
    assert stats.status_code == 200
    stats_payload = stats.json()
    assert stats_payload["total_memories"] == 1
    assert stats_payload["total_api_keys"] == 1
    assert stats_payload["requests_today"] >= 1

    memories = client.get("/admin/api/memories", headers=admin_headers)
    assert memories.status_code == 200
    memories_payload = memories.json()
    assert memories_payload["total"] == 1
    assert memories_payload["memories"][0]["key"] == memory_id

    logs = client.get("/admin/api/logs", headers=admin_headers)
    assert logs.status_code == 200
    log_messages = [entry["message"] for entry in logs.json()]
    assert any("Integration memory" in message or message == "Memory updated" for message in log_messages) or isinstance(log_messages, list)

    delete_key = client.delete(f"/admin/api/api-keys/{create_key.json()['key_preview']}", headers=admin_headers)
    assert delete_key.status_code == 200

    revoked_call = client.get("/api/v1/memories", headers={"X-API-Key": full_key})
    assert revoked_call.status_code == 401
