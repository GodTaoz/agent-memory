"""MCP Server for Memory MCP Server.

This module implements the Model Context Protocol (MCP) server
for memory operations.
"""

import logging
from typing import Any, Dict, List, Optional

from memory_mcp.engine.memory import MemoryEngine
from memory_mcp.models import Memory

logger = logging.getLogger(__name__)


class MCPServer:
    """MCP Server for memory operations."""

    def __init__(self, engine: MemoryEngine):
        """Initialize MCP server.
        
        Args:
            engine: Memory engine instance
        """
        self._engine = engine
        self.name = "memory-mcp"

    def get_tools(self) -> List[Dict[str, Any]]:
        """Get list of available MCP tools.
        
        Returns:
            List of tool definitions
        """
        return [
            {
                "name": "memory.save",
                "description": "Save a new memory",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "content": {"type": "string", "description": "Memory content"},
                        "tags": {"type": "array", "items": {"type": "string"}, "description": "Tags"},
                        "agent": {"type": "string", "description": "Agent name"},
                        "confidence": {"type": "string", "enum": ["high", "medium", "low"], "description": "Confidence level"}
                    },
                    "required": ["content"]
                }
            },
            {
                "name": "memory.get",
                "description": "Get a memory by ID",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "id": {"type": "string", "description": "Memory ID"}
                    },
                    "required": ["id"]
                }
            },
            {
                "name": "memory.search",
                "description": "Search memories",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "query": {"type": "string", "description": "Search query"},
                        "tags": {"type": "array", "items": {"type": "string"}, "description": "Filter by tags"},
                        "agent": {"type": "string", "description": "Filter by agent"},
                        "limit": {"type": "integer", "description": "Max results", "default": 10}
                    }
                }
            },
            {
                "name": "memory.update",
                "description": "Update an existing memory",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "id": {"type": "string", "description": "Memory ID"},
                        "content": {"type": "string", "description": "New content"},
                        "tags": {"type": "array", "items": {"type": "string"}, "description": "New tags"}
                    },
                    "required": ["id"]
                }
            },
            {
                "name": "memory.delete",
                "description": "Delete a memory",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "id": {"type": "string", "description": "Memory ID"}
                    },
                    "required": ["id"]
                }
            },
            {
                "name": "memory.list",
                "description": "List memories",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "limit": {"type": "integer", "description": "Max results", "default": 10},
                        "offset": {"type": "integer", "description": "Offset", "default": 0}
                    }
                }
            },
            {
                "name": "memory.health",
                "description": "Health check",
                "inputSchema": {
                    "type": "object",
                    "properties": {}
                }
            },
            {
                "name": "memory.stats",
                "description": "Get memory statistics",
                "inputSchema": {
                    "type": "object",
                    "properties": {}
                }
            }
        ]

    def handle_tool_call(
        self,
        tool_name: str,
        arguments: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Handle an MCP tool call.
        
        Args:
            tool_name: Name of the tool to call
            arguments: Tool arguments
            
        Returns:
            Tool result
        """
        try:
            if tool_name == "memory.save":
                return self._handle_save(arguments)
            elif tool_name == "memory.get":
                return self._handle_get(arguments)
            elif tool_name == "memory.search":
                return self._handle_search(arguments)
            elif tool_name == "memory.update":
                return self._handle_update(arguments)
            elif tool_name == "memory.delete":
                return self._handle_delete(arguments)
            elif tool_name == "memory.list":
                return self._handle_list(arguments)
            elif tool_name == "memory.health":
                return self._handle_health(arguments)
            elif tool_name == "memory.stats":
                return self._handle_stats(arguments)
            else:
                return {"error": f"Unknown tool: {tool_name}"}
        except Exception as e:
            logger.error(f"Error handling tool call {tool_name}: {e}")
            return {"error": str(e)}

    def _handle_save(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Handle memory.save tool call."""
        content = arguments.get("content")
        if not content:
            return {"error": "Content is required"}
        
        memory = Memory(
            id=self._engine.generate_id(),
            content=content,
            tags=arguments.get("tags", []),
            agent=arguments.get("agent", "")
        )
        
        success = self._engine.save(memory)
        return {"success": success, "memory": memory.to_dict()}

    def _handle_get(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Handle memory.get tool call."""
        memory_id = arguments.get("id")
        if not memory_id:
            return {"error": "ID is required"}
        
        memory = self._engine.get(memory_id)
        if memory is None:
            return {"error": f"Memory not found: {memory_id}"}
        
        return {"memory": memory.to_dict()}

    def _handle_search(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Handle memory.search tool call."""
        query = arguments.get("query", "")
        tags = arguments.get("tags")
        agent = arguments.get("agent")
        limit = arguments.get("limit", 10)
        
        results = self._engine.search(
            query=query,
            tags=tags,
            agent=agent,
            limit=limit
        )
        
        return {"memories": [m.to_dict() for m in results]}

    def _handle_update(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Handle memory.update tool call."""
        memory_id = arguments.get("id")
        if not memory_id:
            return {"error": "ID is required"}
        
        updates = {}
        if "content" in arguments:
            updates["content"] = arguments["content"]
        if "tags" in arguments:
            updates["tags"] = arguments["tags"]
        
        memory = self._engine.update(memory_id, updates)
        if memory is None:
            return {"error": f"Memory not found: {memory_id}"}
        
        return {"memory": memory.to_dict()}

    def _handle_delete(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Handle memory.delete tool call."""
        memory_id = arguments.get("id")
        if not memory_id:
            return {"error": "ID is required"}
        
        success = self._engine.delete(memory_id)
        return {"success": success}

    def _handle_list(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Handle memory.list tool call."""
        limit = arguments.get("limit", 10)
        offset = arguments.get("offset", 0)
        
        memories = self._engine.list_memories(limit=limit, offset=offset)
        return {"memories": [m.to_dict() for m in memories]}

    def _handle_health(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Handle memory.health tool call."""
        count = self._engine.count()
        return {
            "status": "healthy",
            "total_memories": count
        }

    def _handle_stats(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Handle memory.stats tool call."""
        count = self._engine.count()
        return {
            "total_memories": count
        }
