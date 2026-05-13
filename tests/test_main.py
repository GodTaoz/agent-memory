"""Tests for application entrypoint."""

from unittest.mock import MagicMock, patch

from fastapi import FastAPI


def test_factory_create_app_returns_fastapi_instance():
    """Project entrypoint factory should create a FastAPI app."""
    from memory_mcp.main import create_app

    with patch("memory_mcp.main.RedisBackend") as mock_backend_cls, patch(
        "memory_mcp.main.IndexManager"
    ) as mock_index_cls:
        mock_backend = MagicMock()
        mock_backend._ensure_connected.return_value = MagicMock()
        mock_backend_cls.return_value = mock_backend
        mock_index_cls.return_value = MagicMock()

        app = create_app()

    assert isinstance(app, FastAPI)
    assert app.title == "Memory MCP Server"
    mock_backend.connect.assert_called_once()
