# Release Checklist

Use this checklist before tagging or publishing a release.

## Version and docs

- bump the version in `pyproject.toml`
- update README and any changed docs
- make sure example commands still match the real entrypoints
- summarize notable changes in release notes / changelog text

## Verification commands

Run these from a clean working tree:

```bash
pytest -q
black --check src/memory_mcp/main.py src/memory_mcp/mcp_runtime.py tests/test_mcp_runtime.py examples
flake8 src/memory_mcp/main.py src/memory_mcp/mcp_runtime.py tests/test_mcp_runtime.py examples
mypy src/memory_mcp/main.py src/memory_mcp/mcp_runtime.py
```

These commands match the current CI-enforced runnable surface. Repository-wide lint/type cleanup remains a separate baseline-hardening track.

## Runtime spot checks

Run these with a reachable Redis and any required auth/config already set (for example `REDIS_HOST` and `REDIS_PASSWORD`).

### REST/admin

```bash
uvicorn memory_mcp.main:create_app --factory --host 127.0.0.1 --port 5678
curl http://127.0.0.1:5678/api/v1/health
```

### MCP stdio

```bash
memory-mcp-stdio
```

Use [`examples/mcp_stdio_client.py`](../examples/mcp_stdio_client.py) or your MCP client of choice to verify tool discovery and one `memory.health` call.

## Packaging

- confirm editable install works: `pip install -e '.[all]'`
- confirm console scripts exist: `memory-mcp`, `memory-mcp-stdio`
- confirm Docker build still succeeds if container deployment is documented

## Final review

- confirm `git status --short` is clean
- confirm CI is green on the final commit
- confirm the branch contains all intended docs/tests/examples
