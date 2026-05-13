# Architecture Overview

`agent-memory` is a local-first memory service for AI agents. It currently ships a verified FastAPI runtime for REST/admin access and also contains MCP-facing tool definitions that still need a dedicated transport/bootstrap entrypoint.

- a REST API for general-purpose clients and automation
- an MCP protocol surface in `src/memory_mcp/protocol/mcp.py` for future agent-native tool integrations

## High-level layout

```text
Clients
  ├─ REST clients
  ├─ MCP clients
  └─ Browser admin panel
           │
           ▼
    FastAPI application (`memory_mcp.main:create_app`)
           │
           ├─ REST routes (`src/memory_mcp/protocol/rest.py`)
           ├─ Admin routes (`src/memory_mcp/admin/routes.py`)
           ├─ Auth / API key handling (`src/memory_mcp/auth/`, `src/memory_mcp/admin/`)
           └─ Memory engine (`src/memory_mcp/engine/`)
                      │
                      ├─ Redis backend (`src/memory_mcp/storage/redis_backend.py`)
                      └─ Index manager (`src/memory_mcp/storage/index.py`)
```

## Main runtime flow

1. `memory_mcp.main:create_app()` loads config from `config/config.yaml` plus environment overrides.
2. The app creates a Redis backend and connects immediately.
3. An `IndexManager` and `MemoryEngine` are constructed on top of the backend.
4. FastAPI mounts:
   - the memory REST API
   - the admin API
   - the built admin frontend assets when available
5. Clients interact with the running service through REST today; MCP contract parity work builds on the same engine.

## Component responsibilities

### `src/memory_mcp/main.py`
- application factory
- startup wiring
- console-script entrypoint

### `src/memory_mcp/protocol/`
- `rest.py`: REST endpoints and response models
- `mcp.py`: MCP tool definitions and tool-call dispatch

### `src/memory_mcp/engine/`
- memory CRUD orchestration
- search and evolution helpers
- translation between storage primitives and domain models

### `src/memory_mcp/storage/`
- `redis_backend.py`: persistence and Redis connectivity
- `index.py`: secondary indexes for tag/agent/search access patterns

### `src/memory_mcp/admin/`
- admin authentication
- API key management
- admin routes and logging
- dashboard/backend support for the web panel

### `src/memory_mcp/auth/`
- API-key middleware
- ACL foundation for multi-agent isolation work

## Persistence model

The service currently uses two persistence layers:

- **Redis** for memory data and indexes
- **local files / SQLite** for admin credentials, API key state, and admin logs

By default, admin password state and managed API keys resolve under the project `data/` directory, while admin logs use `data/admin_logs.db` relative to the process working directory unless overridden.

This split keeps memory operations lightweight while allowing the admin surface to persist local operational state.

## Current architectural priorities

The current roadmap focuses on strengthening:

1. development bootstrap and verification ergonomics
2. REST/MCP contract parity
3. multi-agent isolation semantics
4. deployment and operator readiness

Those improvements build on the current architecture rather than replacing it.
