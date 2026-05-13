# Contributing

Thanks for your interest in contributing to `agent-memory`.

## Development workflow

1. Work from the `master` branch.
2. Create a feature branch for non-trivial changes.
3. Add or update tests before changing behavior.
4. Run verification locally:
   ```bash
   pytest
   black src tests
   flake8 src tests
   mypy src
   ```
5. Keep docs and config examples in sync with code changes.

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
