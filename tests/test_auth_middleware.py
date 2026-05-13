"""Tests for authentication middleware."""

import pytest
from unittest.mock import MagicMock
from fastapi.testclient import TestClient
from memory_mcp.auth.middleware import AuthMiddleware
from memory_mcp.protocol.rest import create_app


class TestAuthMiddleware:
    """Test AuthMiddleware class."""

    def test_init(self):
        """Test initializing auth middleware."""
        config = {
            "api_keys": ["test-key-123", "test-key-456"]
        }
        middleware = AuthMiddleware(config)
        
        assert middleware._api_keys == ["test-key-123", "test-key-456"]

    def test_validate_api_key_valid(self):
        """Test validating a valid API key."""
        config = {
            "api_keys": ["test-key-123"]
        }
        middleware = AuthMiddleware(config)
        
        assert middleware.validate_api_key("test-key-123") is True

    def test_validate_api_key_invalid(self):
        """Test validating an invalid API key."""
        config = {
            "api_keys": ["test-key-123"]
        }
        middleware = AuthMiddleware(config)
        
        assert middleware.validate_api_key("invalid-key") is False

    def test_validate_api_key_empty(self):
        """Test validating an empty API key."""
        config = {
            "api_keys": ["test-key-123"]
        }
        middleware = AuthMiddleware(config)
        
        assert middleware.validate_api_key("") is False
        assert middleware.validate_api_key(None) is False

    def test_validate_api_key_no_config(self):
        """Test when no API keys configured (allow all)."""
        config = {}
        middleware = AuthMiddleware(config)
        
        # When no API keys configured, allow all
        assert middleware.validate_api_key("any-key") is True

    def test_extract_api_key_from_header(self):
        """Test extracting API key from Authorization header."""
        config = {"api_keys": ["test-key"]}
        middleware = AuthMiddleware(config)
        
        # Test Bearer token format
        key = middleware.extract_api_key({"authorization": "Bearer test-key"})
        assert key == "test-key"

    def test_extract_api_key_from_query(self):
        """Test extracting API key from query parameter."""
        config = {"api_keys": ["test-key"]}
        middleware = AuthMiddleware(config)
        
        key = middleware.extract_api_key({}, query_params={"api_key": "test-key"})
        assert key == "test-key"

    def test_extract_api_key_missing(self):
        """Test extracting API key when missing."""
        config = {"api_keys": ["test-key"]}
        middleware = AuthMiddleware(config)
        
        key = middleware.extract_api_key({}, query_params={})
        assert key is None


class TestAuthIntegration:
    """Test authentication integration with REST API."""

    def test_request_without_api_key_when_required(self):
        """Test request without API key when required."""
        mock_engine = MagicMock()
        mock_engine.count.return_value = 0
        
        auth_config = {
            "api_keys": ["test-key-123"]
        }
        
        app = create_app(mock_engine, auth_config=auth_config)
        client = TestClient(app)
        
        # Request without API key should fail
        response = client.get("/api/v1/health")
        assert response.status_code == 401

    def test_request_with_valid_api_key(self):
        """Test request with valid API key."""
        mock_engine = MagicMock()
        mock_engine.count.return_value = 0
        
        auth_config = {
            "api_keys": ["test-key-123"]
        }
        
        app = create_app(mock_engine, auth_config=auth_config)
        client = TestClient(app)
        
        # Request with valid API key should succeed
        response = client.get(
            "/api/v1/health",
            headers={"Authorization": "Bearer test-key-123"}
        )
        assert response.status_code == 200

    def test_request_with_invalid_api_key(self):
        """Test request with invalid API key."""
        mock_engine = MagicMock()
        mock_engine.count.return_value = 0
        
        auth_config = {
            "api_keys": ["test-key-123"]
        }
        
        app = create_app(mock_engine, auth_config=auth_config)
        client = TestClient(app)
        
        # Request with invalid API key should fail
        response = client.get(
            "/api/v1/health",
            headers={"Authorization": "Bearer invalid-key"}
        )
        assert response.status_code == 401

    def test_request_with_api_key_in_query(self):
        """Test request with API key in query parameter."""
        mock_engine = MagicMock()
        mock_engine.count.return_value = 0
        
        auth_config = {
            "api_keys": ["test-key-123"]
        }
        
        app = create_app(mock_engine, auth_config=auth_config)
        client = TestClient(app)
        
        # Request with API key in query should succeed
        response = client.get("/api/v1/health?api_key=test-key-123")
        assert response.status_code == 200

    def test_request_without_auth_when_not_configured(self):
        """Test request without auth when not configured."""
        mock_engine = MagicMock()
        mock_engine.count.return_value = 0
        
        # No auth config
        app = create_app(mock_engine)
        client = TestClient(app)
        
        # Request without API key should succeed when auth not configured
        response = client.get("/api/v1/health")
        assert response.status_code == 200
