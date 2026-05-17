"""Tests for the runnable MCP stdio runtime."""

from unittest.mock import MagicMock, patch

import pytest
from mcp.server.fastmcp.exceptions import ToolError


@pytest.mark.asyncio
async def test_create_mcp_app_registers_expected_memory_tools():
    """The stdio runtime should expose the documented memory.* tool surface."""
    from memory_mcp.mcp_runtime import create_mcp_app

    engine = MagicMock()
    app = create_mcp_app(engine)

    tool_names = sorted(tool.name for tool in await app.list_tools())

    assert tool_names == [
        "memory.delete",
        "memory.get",
        "memory.health",
        "memory.list",
        "memory.save",
        "memory.search",
        "memory.stats",
        "memory.update",
    ]


@pytest.mark.asyncio
async def test_create_mcp_app_save_tool_delegates_to_memory_engine():
    """The stdio runtime should delegate tool calls through adapter semantics."""
    from memory_mcp.mcp_runtime import create_mcp_app

    engine = MagicMock()
    engine.generate_id.return_value = "mem_stdio"
    engine.save.return_value = True

    app = create_mcp_app(engine)
    result = await app.call_tool(
        "memory.save",
        {
            "content": "Remember MCP stdio support",
            "tags": ["mcp", "runtime"],
            "agent": "tester",
            "confidence": "medium",
        },
    )
    structured_result = result[1]

    assert structured_result["success"] is True
    assert structured_result["memory"]["id"] == "mem_stdio"
    assert engine.save.call_args.args[0].confidence.value == "medium"


def test_run_stdio_bootstraps_engine_and_uses_stdio_transport():
    """The stdio runner should bootstrap the shared engine and run FastMCP on stdio."""
    from memory_mcp.mcp_runtime import run_stdio

    app = MagicMock()

    with (
        patch(
            "memory_mcp.mcp_runtime.create_engine", return_value=MagicMock()
        ) as create_engine_mock,
        patch(
            "memory_mcp.mcp_runtime.create_mcp_app", return_value=app
        ) as create_mcp_app_mock,
    ):
        run_stdio()

    create_engine_mock.assert_called_once_with()
    create_mcp_app_mock.assert_called_once_with(create_engine_mock.return_value)
    app.run.assert_called_once_with(transport="stdio")


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("tool_name", "expected_field"),
    [
        ("memory.save", "content"),
        ("memory.get", "id"),
    ],
)
async def test_create_mcp_app_uses_fastmcp_required_argument_validation(
    tool_name,
    expected_field,
):
    """The runtime should surface FastMCP required-argument validation."""
    from memory_mcp.mcp_runtime import create_mcp_app

    app = create_mcp_app(MagicMock())

    with pytest.raises(ToolError, match=expected_field):
        await app.call_tool(tool_name, {})
