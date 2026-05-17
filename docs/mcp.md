# MCP Runtime Guide

`agent-memory` now ships a verified **stdio MCP runtime** in addition to the FastAPI REST/admin service.

## Verified runtime entrypoint

After installation, start the MCP server with:

```bash
# requires the same Redis/config setup as the REST runtime
memory-mcp-stdio
```

This console script runs the FastMCP-based stdio server defined in `src/memory_mcp/mcp_runtime.py`.

## Available tools

The runtime exposes these tool names:

- `memory.save`
- `memory.get`
- `memory.search`
- `memory.update`
- `memory.delete`
- `memory.list`
- `memory.health`
- `memory.stats`

These tools delegate to the same `MemoryEngine` core used by the REST service.

## Installation

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -e '.[all]'
```

## Example: local smoke check with Python client

See [`examples/mcp_stdio_client.py`](../examples/mcp_stdio_client.py) for a minimal stdio client.

## Hermes Agent configuration example

```yaml
mcp_servers:
  agent_memory:
    command: "memory-mcp-stdio"
    timeout: 120
    connect_timeout: 30
    env:
      REDIS_HOST: "127.0.0.1"
      REDIS_PORT: "6379"
      REDIS_PASSWORD: ""
```

If `memory-mcp-stdio` is inside a virtual environment, use the absolute path to the script or invoke the venv Python explicitly.

## Behavior notes

- required arguments are validated by FastMCP before tool execution
- tool handlers preserve the existing `memory.*` semantics from `protocol/mcp.py`
- invalid enum-like values such as unsupported `confidence` values are still reported through the underlying adapter logic
- the stdio runtime is test-covered by `tests/test_mcp_runtime.py`

## Verification commands

```bash
pytest -q tests/test_mcp.py tests/test_protocol_parity.py tests/test_mcp_runtime.py
```

## Current scope

This guide covers the verified stdio runtime. REST/admin remains the recommended path for browser-based inspection and operational workflows.
