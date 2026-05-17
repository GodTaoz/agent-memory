"""Runnable MCP stdio runtime for agent-memory."""

from __future__ import annotations

from typing import Any, Optional

from mcp.server.fastmcp import FastMCP

from memory_mcp.engine.memory import MemoryEngine
from memory_mcp.main import create_engine
from memory_mcp.protocol.mcp import MCPServer

SERVER_INSTRUCTIONS = (
    "agent-memory MCP stdio runtime exposing the same memory.* tool surface "
    "as the documented in-process MCP adapter."
)


def create_mcp_app(engine: Optional[MemoryEngine] = None) -> FastMCP:
    """Create a runnable FastMCP stdio application backed by the shared engine."""
    runtime_engine = engine or create_engine()
    adapter = MCPServer(runtime_engine)
    app = FastMCP(name=adapter.name, instructions=SERVER_INSTRUCTIONS)

    def call(tool_name: str, arguments: dict[str, Any]) -> dict[str, Any]:
        return adapter.handle_tool_call(tool_name, arguments)

    @app.tool(name="memory.save", description="Save a new memory")
    def memory_save(
        content: str,
        tags: Optional[list[str]] = None,
        agent: str = "",
        confidence: str = "high",
    ) -> dict[str, Any]:
        return call(
            "memory.save",
            {
                "content": content,
                "tags": tags or [],
                "agent": agent,
                "confidence": confidence,
            },
        )

    @app.tool(name="memory.get", description="Get a memory by ID")
    def memory_get(id: str) -> dict[str, Any]:
        return call("memory.get", {"id": id})

    @app.tool(name="memory.search", description="Search memories")
    def memory_search(
        query: str = "",
        tags: Optional[list[str]] = None,
        agent: Optional[str] = None,
        limit: int = 10,
    ) -> dict[str, Any]:
        return call(
            "memory.search",
            {
                "query": query,
                "tags": tags,
                "agent": agent,
                "limit": limit,
            },
        )

    @app.tool(name="memory.update", description="Update an existing memory")
    def memory_update(
        id: str,
        content: Optional[str] = None,
        tags: Optional[list[str]] = None,
        confidence: Optional[str] = None,
        metadata: Optional[dict[str, Any]] = None,
    ) -> dict[str, Any]:
        arguments: dict[str, Any] = {"id": id}
        if content is not None:
            arguments["content"] = content
        if tags is not None:
            arguments["tags"] = tags
        if confidence is not None:
            arguments["confidence"] = confidence
        if metadata is not None:
            arguments["metadata"] = metadata
        return call("memory.update", arguments)

    @app.tool(name="memory.delete", description="Delete a memory")
    def memory_delete(id: str) -> dict[str, Any]:
        return call("memory.delete", {"id": id})

    @app.tool(name="memory.list", description="List memories")
    def memory_list(limit: int = 10, offset: int = 0) -> dict[str, Any]:
        return call("memory.list", {"limit": limit, "offset": offset})

    @app.tool(name="memory.health", description="Health check")
    def memory_health() -> dict[str, Any]:
        return call("memory.health", {})

    @app.tool(name="memory.stats", description="Get memory statistics")
    def memory_stats() -> dict[str, Any]:
        return call("memory.stats", {})

    return app


def run_stdio() -> None:
    """Run the MCP server over stdio transport."""
    app = create_mcp_app(create_engine())
    app.run(transport="stdio")
