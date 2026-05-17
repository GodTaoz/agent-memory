# M4 Runnable Project Closure Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Close the remaining adoption/runtime gaps so agent-memory is runnable and documented as both a REST service and an MCP stdio server.

**Architecture:** Keep the existing `MemoryEngine` as the shared core. Add a thin MCP stdio runtime that adapts the existing engine/tools to `FastMCP`, then add verification/docs/CI artifacts around that runtime so README claims are executable.

**Tech Stack:** Python 3.10+, FastAPI, FastMCP, pytest, GitHub Actions, Markdown docs.

---

### Task 1: Add MCP stdio runtime entrypoint

**Files:**
- Create: `src/memory_mcp/mcp_runtime.py`
- Modify: `src/memory_mcp/main.py`
- Modify: `pyproject.toml`
- Test: `tests/test_mcp_runtime.py`

- [x] Write failing tests for a FastMCP factory / stdio runner / console entrypoint wiring.
- [x] Run focused tests and verify RED.
- [x] Implement minimal MCP runtime using existing engine bootstrap and MCP tool semantics.
- [x] Re-run focused tests to GREEN.

### Task 2: Add CI verification workflow

**Files:**
- Create: `.github/workflows/ci.yml`
- Modify: `README.md`
- Modify: `CONTRIBUTING.md`

- [x] Add push/PR workflow covering install + pytest + black --check + flake8 + mypy.
- [x] Verify local commands match the workflow.
- [x] Update docs so contributor guidance and CI are consistent.

### Task 3: Add missing protocol and operator docs

**Files:**
- Create: `docs/api.md`
- Create: `docs/mcp.md`
- Create: `docs/deployment.md`
- Create: `docs/release-checklist.md`
- Modify: `README.md`

- [x] Document REST endpoints and auth usage.
- [x] Document verified MCP stdio runtime, startup command, and current scope.
- [x] Document Linux/Docker/NAS deployment plus backup/restore paths.
- [x] Add release checklist with exact verification commands.

### Task 4: Add runnable examples

**Files:**
- Create: `examples/rest_client.py`
- Create: `examples/mcp_stdio_client.py`
- Create: `examples/hermes_agent.md`
- Modify: `README.md`

- [x] Add a Python REST example that saves/searches memory.
- [x] Add a Python MCP stdio example showing process launch and tool call flow.
- [x] Add a Hermes Agent integration example snippet.
- [x] Link all examples from the README.

### Task 5: End-to-end verification and review

**Files:**
- Modify as needed based on review feedback.

- [x] Run focused new tests.
- [x] Run full test suite.
- [x] Run `black --check src/memory_mcp/main.py src/memory_mcp/mcp_runtime.py tests/test_mcp_runtime.py examples`.
- [x] Run `flake8 src/memory_mcp/main.py src/memory_mcp/mcp_runtime.py tests/test_mcp_runtime.py examples`.
- [x] Run `mypy src/memory_mcp/main.py src/memory_mcp/mcp_runtime.py`.
- [x] Request code review and address findings before final summary.
