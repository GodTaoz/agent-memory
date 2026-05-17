# Contributing

Thanks for your interest in contributing to `agent-memory`.

## Development workflow

1. Work from the `master` branch.
2. Create a feature branch for non-trivial changes.
3. Add or update tests before changing behavior.
4. Run verification locally:
   ```bash
   pytest -q
   black --check src/memory_mcp/main.py src/memory_mcp/mcp_runtime.py tests/test_mcp_runtime.py examples
   flake8 src/memory_mcp/main.py src/memory_mcp/mcp_runtime.py tests/test_mcp_runtime.py examples
   mypy src/memory_mcp/main.py src/memory_mcp/mcp_runtime.py
   ```
5. Keep docs and config examples in sync with code changes.
6. Note that repository-wide lint/type cleanup still has historical baseline debt; current CI enforces the runnable-surface checks above plus the full test suite.

## Scope expectations

Good contributions include:

- bug fixes with regression tests
- admin panel improvements
- MCP / REST interoperability improvements
- deployment and security hardening
- search / indexing enhancements
- documentation improvements

## Style notes

- Prefer small, focused commits
- Keep interfaces simple
- Avoid introducing paid external dependencies unless clearly justified
- Preserve the project’s local-first, zero-API-cost positioning
