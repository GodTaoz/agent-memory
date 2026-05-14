"""Tests for application entrypoint."""

from pathlib import Path
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


def test_load_permissions_config_returns_empty_when_missing(tmp_path: Path):
    """Missing config/permissions.yaml should produce an empty ACL config."""
    from memory_mcp.main import _load_permissions_config

    with patch("memory_mcp.main._project_root", return_value=tmp_path):
        assert _load_permissions_config() == {}


def test_load_permissions_config_reads_permissions_yaml(tmp_path: Path):
    """ACL config should be loaded from config/permissions.yaml when present."""
    from memory_mcp.main import _load_permissions_config

    permissions_dir = tmp_path / "config"
    permissions_dir.mkdir(parents=True)
    permissions_file = permissions_dir / "permissions.yaml"
    permissions_file.write_text(
        "shared_namespaces:\n"
        "  - shared\n"
        "agents:\n"
        "  default:\n"
        "    permissions:\n"
        '      namespace: "${agent_id}:*"\n'
        "      operations: [read, write]\n",
        encoding="utf-8",
    )

    with patch("memory_mcp.main._project_root", return_value=tmp_path):
        assert _load_permissions_config() == {
            "shared_namespaces": ["shared"],
            "agents": {
                "default": {
                    "permissions": {
                        "namespace": "${agent_id}:*",
                        "operations": ["read", "write"],
                    }
                }
            },
        }


def test_factory_create_app_loads_acl_from_permissions_yaml():
    """Project entrypoint should load ACL config from config/permissions.yaml."""
    from memory_mcp.main import create_app

    acl_config = {
        "shared_namespaces": ["shared", "team"],
        "agents": {
            "default": {
                "permissions": {
                    "namespace": "${agent_id}:*",
                    "operations": ["read", "write"],
                }
            }
        },
    }

    with patch("memory_mcp.main.RedisBackend") as mock_backend_cls, patch(
        "memory_mcp.main.IndexManager"
    ) as mock_index_cls, patch(
        "memory_mcp.main._load_permissions_config",
        return_value=acl_config,
    ):
        mock_backend = MagicMock()
        mock_backend._ensure_connected.return_value = MagicMock()
        mock_backend_cls.return_value = mock_backend
        mock_index_cls.return_value = MagicMock()

        app = create_app()

    assert app.state.acl._config == acl_config
    assert app.state.auth_middleware._acl._config == acl_config
