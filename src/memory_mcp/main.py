"""Application entrypoint for Memory MCP Server."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any, Dict, Optional

import uvicorn
import yaml

from memory_mcp.config import load_config
from memory_mcp.engine.memory import MemoryEngine
from memory_mcp.protocol.rest import create_app as create_rest_app
from memory_mcp.storage.index import IndexManager
from memory_mcp.storage.redis_backend import RedisBackend


def _load_permissions_config(path: Optional[Path]) -> Optional[Dict[str, Any]]:
    """Load ACL permissions config from YAML if present."""
    if path is None or not path.exists():
        return None

    with path.open("r", encoding="utf-8") as handle:
        data = yaml.safe_load(handle) or {}

    if not isinstance(data, dict):
        raise ValueError(f"Invalid permissions.yaml at {path}: top-level YAML value must be a mapping")

    return data


def _load_auth_config() -> Dict[str, Any]:
    """Load API key configuration from environment variables and optional ACL config."""
    api_keys = [key.strip() for key in os.environ.get("API_KEYS", "").split(",") if key.strip()]
    auth_config: Dict[str, Any] = {"api_keys": api_keys}

    permissions_path = _project_root() / "config" / "permissions.yaml"
    acl_config = _load_permissions_config(permissions_path)
    if acl_config is not None:
        auth_config["acl"] = acl_config

    return auth_config


def _project_root() -> Path:
    return Path(__file__).resolve().parents[2]


def create_app():
    """Factory for creating the FastAPI application."""
    config_path = _project_root() / "config" / "config.yaml"

    config = load_config(str(config_path) if config_path.exists() else None, use_env=True)

    backend = RedisBackend(
        host=config.redis_host,
        port=config.redis_port,
        password=config.redis_password,
        db=config.redis_db,
        key_prefix=config.redis_key_prefix,
    )
    backend.connect()

    index = IndexManager(backend._ensure_connected(), prefix=config.redis_key_prefix)
    engine = MemoryEngine(backend, index)

    return create_rest_app(engine, auth_config=_load_auth_config())


def run() -> None:
    """Run the application server."""
    config_path = _project_root() / "config" / "config.yaml"
    config = load_config(str(config_path) if config_path.exists() else None, use_env=True)
    uvicorn.run(
        "memory_mcp.main:create_app",
        factory=True,
        host=config.server_host,
        port=config.server_port,
        workers=config.server_workers,
    )


def cli() -> None:
    """Backward-compatible console entrypoint."""
    run()
