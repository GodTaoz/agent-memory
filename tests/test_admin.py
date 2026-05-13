"""Tests for admin panel."""

from unittest.mock import MagicMock

import pytest
from fastapi.testclient import TestClient

from memory_mcp.admin import auth as admin_auth_module
from memory_mcp.admin.auth import AdminAuth


class TestAdminAuth:
    """Test admin authentication."""

    def test_default_password_verification(self):
        """Test default password verification."""
        auth = AdminAuth()
        assert auth.verify_password("admin123") is True
        assert auth.verify_password("wrong") is False

    def test_detects_default_password_state(self, tmp_path, monkeypatch):
        """Fresh instances should report that the default password is still active."""
        monkeypatch.setenv("ADMIN_AUTH_CONFIG_PATH", str(tmp_path / "admin_auth.json"))
        monkeypatch.delenv("ADMIN_PASSWORD_HASH", raising=False)
        monkeypatch.delenv("ADMIN_PASSWORD_SALT", raising=False)

        auth = AdminAuth()

        assert auth.is_default_password() is True
        assert auth.requires_password_change() is True

    def test_create_session(self):
        """Test session creation."""
        auth = AdminAuth()
        token = auth.create_session("admin123")

        assert token is not None
        assert len(token) > 0
        assert auth.verify_session(token) is True

    def test_invalid_session(self):
        """Test invalid session verification."""
        auth = AdminAuth()
        assert auth.verify_session("invalid-token") is False

    def test_revoke_session(self):
        """Test session revocation."""
        auth = AdminAuth()
        token = auth.create_session("admin123")

        assert auth.revoke_session(token) is True
        assert auth.verify_session(token) is False

    def test_revoke_nonexistent_session(self):
        """Test revoking nonexistent session."""
        auth = AdminAuth()
        assert auth.revoke_session("nonexistent") is False

    def test_get_active_sessions(self):
        """Test getting active sessions."""
        auth = AdminAuth()

        # Create multiple sessions
        auth.create_session("admin123")
        auth.create_session("admin123")

        sessions = auth.get_active_sessions()
        assert len(sessions) == 2

    def test_revoke_all_sessions(self):
        """Test revoking all sessions."""
        auth = AdminAuth()

        # Create multiple sessions
        auth.create_session("admin123")
        auth.create_session("admin123")

        count = auth.revoke_all_sessions()
        assert count == 2
        assert len(auth.get_active_sessions()) == 0

    def test_change_password_persists_across_instances(self, tmp_path, monkeypatch):
        """Changed admin password should persist and be loaded by a new instance."""
        config_path = tmp_path / "admin_auth.json"
        monkeypatch.setenv("ADMIN_AUTH_CONFIG_PATH", str(config_path))
        monkeypatch.delenv("ADMIN_PASSWORD_HASH", raising=False)
        monkeypatch.delenv("ADMIN_PASSWORD_SALT", raising=False)

        auth = AdminAuth()
        assert auth.change_password("admin123", "new-secret-456") is True
        assert auth.is_default_password() is False
        assert auth.requires_password_change() is False

        reloaded = AdminAuth()
        assert reloaded.verify_password("admin123") is False
        assert reloaded.verify_password("new-secret-456") is True
        assert reloaded.is_default_password() is False
        assert config_path.exists() is True

    def test_password_file_permissions_are_restricted(self, tmp_path, monkeypatch):
        """Persisted password file should be owner-read/write only."""
        config_path = tmp_path / "admin_auth.json"
        monkeypatch.setenv("ADMIN_AUTH_CONFIG_PATH", str(config_path))
        monkeypatch.delenv("ADMIN_PASSWORD_HASH", raising=False)
        monkeypatch.delenv("ADMIN_PASSWORD_SALT", raising=False)

        auth = AdminAuth()
        assert auth.change_password("admin123", "new-secret-456") is True

        assert oct(config_path.stat().st_mode & 0o777) == "0o600"

    def test_failed_login_attempts_trigger_lockout(self, tmp_path, monkeypatch):
        """Repeated login failures should temporarily lock the admin account."""
        monkeypatch.setenv("ADMIN_AUTH_CONFIG_PATH", str(tmp_path / "admin_auth.json"))
        monkeypatch.delenv("ADMIN_PASSWORD_HASH", raising=False)
        monkeypatch.delenv("ADMIN_PASSWORD_SALT", raising=False)

        auth = AdminAuth()
        for _ in range(auth.MAX_FAILED_ATTEMPTS):
            assert auth.create_session("wrong-password") is None

        assert auth.is_locked_out() is True
        assert auth.create_session("admin123") is None

    def test_default_persisted_config_path_is_project_relative(self):
        """Default persisted auth config path should live under the project data dir."""
        auth = AdminAuth()
        expected_path = (
            admin_auth_module.Path(admin_auth_module.__file__).resolve().parents[3]
            / "data"
            / "admin_auth.json"
        )

        assert auth._config_path.is_absolute() is True
        assert auth._config_path == expected_path


class TestAdminRoutes:
    """Test admin API routes."""

    @pytest.fixture
    def admin_auth(self):
        """Create admin auth instance."""
        from memory_mcp.admin.auth import AdminAuth

        return AdminAuth()

    @pytest.fixture
    def client(self, admin_auth):
        """Create test client."""
        from fastapi import FastAPI
        from memory_mcp.admin.routes import router
        from memory_mcp.admin.deps import get_admin_auth

        app = FastAPI()
        app.include_router(router)
        app.state.memory_engine = MagicMock()
        app.state.memory_engine.count.return_value = 0
        app.state.memory_engine.list_memories.return_value = []
        app.state.memory_engine.search.return_value = []
        app.state.memory_engine.get.return_value = None
        app.state.memory_engine.update.return_value = None
        app.state.memory_engine.delete.return_value = False

        # Override the dependency to use the same instance
        app.dependency_overrides[get_admin_auth] = lambda: admin_auth

        return TestClient(app)

    @pytest.fixture
    def auth_headers(self, admin_auth):
        """Get auth headers."""
        token = admin_auth.create_session("admin123")
        return {"Authorization": f"Bearer {token}"}

    def test_login_success(self, client):
        """Test successful login."""
        response = client.post("/admin/api/auth/login", json={"password": "admin123"})

        assert response.status_code == 200
        data = response.json()
        assert "token" in data
        assert data["expires_in"] > 0

    def test_login_failure(self, client):
        """Test failed login."""
        response = client.post("/admin/api/auth/login", json={"password": "wrong"})

        assert response.status_code == 401

    def test_login_rate_limit_after_repeated_failures(self, client):
        """Repeated failed login attempts should return 429 once locked."""
        for _ in range(5):
            response = client.post("/admin/api/auth/login", json={"password": "wrong"})

        assert response.status_code == 429

    def test_get_stats(self, client, auth_headers):
        """Test getting system stats."""
        response = client.get("/admin/api/stats", headers=auth_headers)

        assert response.status_code == 200
        data = response.json()
        assert "redis_connected" in data
        assert "total_memories" in data

    def test_get_stats_unauthorized(self, client):
        """Test getting stats without auth."""
        response = client.get("/admin/api/stats")

        assert response.status_code == 401

    def test_get_memories(self, client, auth_headers):
        """Test getting memories."""
        response = client.get("/admin/api/memories", headers=auth_headers)

        assert response.status_code == 200
        payload = response.json()
        assert isinstance(payload["memories"], list)
        assert isinstance(payload["total"], int)

    def test_get_agents(self, client, auth_headers):
        """Test getting agents."""
        response = client.get("/admin/api/agents", headers=auth_headers)

        assert response.status_code == 200
        assert isinstance(response.json(), list)

    def test_get_logs(self, client, auth_headers):
        """Test getting logs."""
        response = client.get("/admin/api/logs", headers=auth_headers)

        assert response.status_code == 200
        assert isinstance(response.json(), list)
