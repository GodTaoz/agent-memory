"""Tests for admin panel."""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock

from memory_mcp.admin.auth import AdminAuth


class TestAdminAuth:
    """Test admin authentication."""
    
    def test_default_password(self):
        """Test default password verification."""
        auth = AdminAuth()
        assert auth.verify_password("admin123") is True
        assert auth.verify_password("wrong") is False
    
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
        token1 = auth.create_session("admin123")
        token2 = auth.create_session("admin123")
        
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
        assert isinstance(response.json(), list)
    
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
