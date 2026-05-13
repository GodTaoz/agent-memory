"""Tests for admin logs and dashboard routes."""

from __future__ import annotations

from fastapi import FastAPI
from fastapi.testclient import TestClient

from memory_mcp.admin.api_keys import ApiKeyStore
from memory_mcp.admin.auth import AdminAuth
from memory_mcp.admin.deps import get_admin_auth
from memory_mcp.admin.logger import SQLiteLogger
from memory_mcp.admin.routes import router


class FakeRedisClient:
    def ping(self) -> bool:
        return True

    def info(self, section: str | None = None) -> dict:
        return {"used_memory_human": "1.5M"}

    def keys(self, pattern: str) -> list[str]:
        return ["memory:1", "memory:2", "memory:3"]


class FakeBackend:
    def __init__(self) -> None:
        self.key_prefix = "memory"
        self._client = FakeRedisClient()


class FakeMemoryEngine:
    def __init__(self) -> None:
        self._backend = FakeBackend()

    def count(self) -> int:
        return 7

    def list_memories(self, limit: int = 100, offset: int = 0):
        return []

    def search(self, query=None, tags=None, agent=None, limit: int = 10):
        return []

    def get(self, memory_id: str):
        return None

    def update(self, memory_id: str, updates: dict):
        return None

    def delete(self, memory_id: str) -> bool:
        return False


def build_client(tmp_path) -> tuple[TestClient, SQLiteLogger, ApiKeyStore]:
    app = FastAPI()
    app.include_router(router)
    app.state.memory_engine = FakeMemoryEngine()
    app.state.api_key_store = ApiKeyStore(path=str(tmp_path / "api_keys.json"))
    app.state.admin_logger = SQLiteLogger(str(tmp_path / "admin_logs.db"))

    auth = AdminAuth()
    app.dependency_overrides[get_admin_auth] = lambda: auth

    return TestClient(app), app.state.admin_logger, app.state.api_key_store


def test_stats_endpoint_returns_real_counts(tmp_path) -> None:
    client, logger, api_key_store = build_client(tmp_path)
    token = client.app.dependency_overrides[get_admin_auth]().create_session("admin123")
    headers = {"Authorization": f"Bearer {token}"}

    logger.log_operation("info", "memory", "Memory updated")
    logger.log_login(True, ip_address="127.0.0.1")
    logger.log_api_access("GET", "/api/v1/memories", 200, 12.5, api_key_preview="amk_test...")
    api_key_store.create_key("agent-1", permissions="read_write")

    response = client.get("/admin/api/stats", headers=headers)

    assert response.status_code == 200
    payload = response.json()
    assert payload["redis_connected"] is True
    assert payload["redis_memory_used"] == "1.5M"
    assert payload["redis_keys_count"] == 3
    assert payload["total_memories"] == 7
    assert payload["total_api_keys"] == 1
    assert payload["requests_today"] == 1
    assert payload["avg_response_time_ms"] == 12.5
    assert payload["uptime_seconds"] >= 0


def test_logs_endpoint_returns_logged_entries_and_supports_level_filter(tmp_path) -> None:
    client, logger, _ = build_client(tmp_path)
    token = client.app.dependency_overrides[get_admin_auth]().create_session("admin123")
    headers = {"Authorization": f"Bearer {token}"}

    logger.log_operation("info", "memory", "Memory updated", details={"id": "mem_1"}, ip_address="127.0.0.1")
    logger.log_operation("error", "auth", "Invalid password", ip_address="127.0.0.2")

    response = client.get("/admin/api/logs", headers=headers)
    assert response.status_code == 200
    payload = response.json()
    assert len(payload) == 2
    assert payload[0]["message"] in {"Memory updated", "Invalid password"}

    filtered = client.get("/admin/api/logs?level=error", headers=headers)
    assert filtered.status_code == 200
    filtered_payload = filtered.json()
    assert len(filtered_payload) == 1
    assert filtered_payload[0]["level"] == "error"
    assert filtered_payload[0]["message"] == "Invalid password"


def test_login_and_admin_mutations_emit_audit_logs(tmp_path) -> None:
    client, _logger, _ = build_client(tmp_path)

    success = client.post("/admin/api/auth/login", json={"password": "admin123"})
    assert success.status_code == 200
    token = success.json()["token"]
    headers = {"Authorization": f"Bearer {token}"}

    failed = client.post("/admin/api/auth/login", json={"password": "wrong"})
    assert failed.status_code == 401

    created = client.post(
        "/admin/api/api-keys",
        headers=headers,
        json={"name": "audit-agent", "permissions": "read_write"},
    )
    assert created.status_code == 201
    key_preview = created.json()["key_preview"]

    deleted = client.delete(f"/admin/api/api-keys/{key_preview}", headers=headers)
    assert deleted.status_code == 200

    logs = client.get("/admin/api/logs", headers=headers)
    assert logs.status_code == 200
    messages = [entry["message"] for entry in logs.json()]
    assert "Admin login succeeded" in messages
    assert "Admin login failed" in messages
    assert f"Created API key {key_preview}" in messages
    assert f"Deleted API key {key_preview}" in messages
