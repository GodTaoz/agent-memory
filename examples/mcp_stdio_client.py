"""Minimal MCP stdio client example for agent-memory."""

from __future__ import annotations

import json
import os

import anyio
from mcp import ClientSession
from mcp.client.stdio import StdioServerParameters, stdio_client


async def run_example() -> None:
    """Launch the local stdio server and call a couple of tools."""
    server = StdioServerParameters(
        command=os.environ.get("AGENT_MEMORY_MCP_COMMAND", "memory-mcp-stdio"),
        args=[],
        env=os.environ.copy(),
    )

    async with stdio_client(server) as (read_stream, write_stream):
        async with ClientSession(read_stream, write_stream) as session:
            await session.initialize()
            tools = await session.list_tools()
            print("Available tools:")
            print(json.dumps([tool.name for tool in tools.tools], indent=2))

            health = await session.call_tool("memory.health", {})
            print("\nHealth:")
            print(health)

            created = await session.call_tool(
                "memory.save",
                {
                    "content": "Remember MCP stdio support.",
                    "tags": ["mcp", "example"],
                    "agent": "example-client",
                    "confidence": "medium",
                },
            )
            print("\nCreated memory:")
            print(created)


if __name__ == "__main__":
    anyio.run(run_example)
