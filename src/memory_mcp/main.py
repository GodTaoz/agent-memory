"""Application entrypoint for Memory MCP Server."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any, Dict

import uvicorn
import yaml

from memory_mcp.auth.acl import ACL
from memory_mcp.config import load_config
from memory_mcp.engine.memory import MemoryEngine
from memory_mcp.protocol.rest import create_app as create_rest_app
from memory_mcp.storage.index import IndexManager
from memory_mcp.storage.redis_backend import RedisBackend


def _load_auth_config() -> Dict[str, Any]:
    """Load API key configuration from environment variables."""
    api_keys = [key.strip() for key in os.environ.get("API_KEYS", "").split(",") if key.strip()]
    return {"api_keys": api_keys}


def _load_permissions_config() -> Dict[str, Any]:
    """Load ACL configuration from config/permissions.yaml when present."""
    permissions_path = _project_root() / "config" / "permissions.yaml"
    if not permissions_path.exists():
        return {}

    with permissions_path.open("r", encoding="utf-8") as handle:
        return yaml.safe_load(handle) or {}


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

    auth_config = _load_auth_config()
    acl_config = _load_permissions_config()
    if acl_config:
        auth_config["acl"] = ACL(acl_config)

    return create_rest_app(engine, auth_config=auth_config)


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
