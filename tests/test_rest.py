"""Tests for REST API."""

import pytest
from unittest.mock import MagicMock, patch
from fastapi.testclient import TestClient
from memory_mcp.protocol.rest import create_app


class TestRESTAPI:
    """Test REST API endpoints."""

    def test_create_app(self):
        """Test creating FastAPI app."""
        mock_engine = MagicMock()
        app = create_app(mock_engine)
        
        assert app is not None
        assert app.title == "Memory MCP Server"

    def test_root_serves_admin_frontend_when_static_exists(self):
        """Test root route serves built admin frontend."""
        mock_engine = MagicMock()
        app = create_app(mock_engine)
        client = TestClient(app)

        response = client.get("/")

        assert response.status_code == 200
        assert "text/html" in response.headers["content-type"]
        assert "<div id=\"app\"></div>" in response.text

    def test_health_endpoint(self):
        """Test health endpoint."""
        mock_engine = MagicMock()
        mock_engine.count.return_value = 42
        
        app = create_app(mock_engine)
        client = TestClient(app)
        
        response = client.get("/api/v1/health")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["total_memories"] == 42

    def test_stats_endpoint(self):
        """Test stats endpoint."""
        mock_engine = MagicMock()
        mock_engine.count.return_value = 100
        
        app = create_app(mock_engine)
        client = TestClient(app)
        
        response = client.get("/api/v1/stats")
        
        assert response.status_code == 200
        data = response.json()
        assert "total_memories" in data

    def test_create_memory(self):
        """Test creating a memory."""
        mock_engine = MagicMock()
        mock_engine.save.return_value = True
        mock_engine.generate_id.return_value = "mem_123"
        
        app = create_app(mock_engine)
        client = TestClient(app)
        
        response = client.post(
            "/api/v1/memories",
            json={"content": "Test memory", "tags": ["test"]}
        )
        
        assert response.status_code == 201
        data = response.json()
        assert data["content"] == "Test memory"
        mock_engine.save.assert_called_once()

    def test_get_memory(self):
        """Test getting a memory."""
        mock_engine = MagicMock()
        mock_memory = MagicMock()
        mock_memory.to_dict.return_value = {
            "id": "123",
            "content": "Test",
            "tags": [],
            "agent": "",
            "created_at": "2026-01-01T00:00:00",
            "updated_at": "2026-01-01T00:00:00",
            "version": 1,
            "confidence": "high",
            "source": "user",
            "links": [],
            "metadata": {}
        }
        mock_engine.get.return_value = mock_memory
        
        app = create_app(mock_engine)
        client = TestClient(app)
        
        response = client.get("/api/v1/memories/123")
        
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == "123"

    def test_get_memory_not_found(self):
        """Test getting a non-existent memory."""
        mock_engine = MagicMock()
        mock_engine.get.return_value = None
        
        app = create_app(mock_engine)
        client = TestClient(app)
        
        response = client.get("/api/v1/memories/nonexistent")
        
        assert response.status_code == 404

    def test_update_memory(self):
        """Test updating a memory."""
        mock_engine = MagicMock()
        mock_memory = MagicMock()
        mock_memory.to_dict.return_value = {
            "id": "123",
            "content": "Updated",
            "tags": [],
            "agent": "",
            "created_at": "2026-01-01T00:00:00",
            "updated_at": "2026-01-01T00:00:00",
            "version": 2,
            "confidence": "high",
            "source": "user",
            "links": [],
            "metadata": {}
        }
        mock_engine.update.return_value = mock_memory
        
        app = create_app(mock_engine)
        client = TestClient(app)
        
        response = client.put(
            "/api/v1/memories/123",
            json={"content": "Updated"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["content"] == "Updated"

    def test_delete_memory(self):
        """Test deleting a memory."""
        mock_engine = MagicMock()
        mock_engine.delete.return_value = True
        
        app = create_app(mock_engine)
        client = TestClient(app)
        
        response = client.delete("/api/v1/memories/123")
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True

    def test_list_memories(self):
        """Test listing memories."""
        mock_engine = MagicMock()
        mock_engine.list_memories.return_value = [
            MagicMock(to_dict=lambda: {"id": "1", "content": "Memory 1"}),
            MagicMock(to_dict=lambda: {"id": "2", "content": "Memory 2"})
        ]
        
        app = create_app(mock_engine)
        client = TestClient(app)
        
        response = client.get("/api/v1/memories")
        
        assert response.status_code == 200
        data = response.json()
        assert "memories" in data
        assert len(data["memories"]) == 2

    def test_search_memories(self):
        """Test searching memories."""
        mock_engine = MagicMock()
        mock_engine.search.return_value = [
            MagicMock(to_dict=lambda: {"id": "1", "content": "Result 1"})
        ]
        
        app = create_app(mock_engine)
        client = TestClient(app)
        
        response = client.get("/api/v1/memories?q=test")
        
        assert response.status_code == 200
        data = response.json()
        assert "memories" in data
