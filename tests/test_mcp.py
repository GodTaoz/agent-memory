"""Tests for MCP server."""

import pytest
from unittest.mock import MagicMock, patch
from memory_mcp.protocol.mcp import MCPServer


class TestMCPServer:
    """Test MCPServer class."""

    def test_init(self):
        """Test initializing MCP server."""
        mock_engine = MagicMock()
        server = MCPServer(mock_engine)
        
        assert server._engine == mock_engine
        assert server.name == "memory-mcp"

    def test_get_tools(self):
        """Test getting list of available tools."""
        mock_engine = MagicMock()
        server = MCPServer(mock_engine)
        
        tools = server.get_tools()
        
        # Should have at least 8 tools
        assert len(tools) >= 8
        
        # Check tool names
        tool_names = [t["name"] for t in tools]
        assert "memory.save" in tool_names
        assert "memory.search" in tool_names
        assert "memory.get" in tool_names
        assert "memory.update" in tool_names
        assert "memory.delete" in tool_names
        assert "memory.list" in tool_names
        assert "memory.health" in tool_names
        assert "memory.stats" in tool_names

    def test_handle_save(self):
        """Test handling save tool call."""
        mock_engine = MagicMock()
        mock_engine.save.return_value = True
        
        server = MCPServer(mock_engine)
        
        result = server.handle_tool_call(
            "memory.save",
            {"content": "Test memory", "tags": ["test"]}
        )
        
        assert result["success"] is True
        mock_engine.save.assert_called_once()

    def test_handle_get(self):
        """Test handling get tool call."""
        mock_engine = MagicMock()
        mock_memory = MagicMock()
        mock_memory.to_dict.return_value = {"id": "123", "content": "Test"}
        mock_engine.get.return_value = mock_memory
        
        server = MCPServer(mock_engine)
        
        result = server.handle_tool_call(
            "memory.get",
            {"id": "123"}
        )
        
        assert "memory" in result
        mock_engine.get.assert_called_once_with("123")

    def test_handle_get_not_found(self):
        """Test handling get tool call for non-existent memory."""
        mock_engine = MagicMock()
        mock_engine.get.return_value = None
        
        server = MCPServer(mock_engine)
        
        result = server.handle_tool_call(
            "memory.get",
            {"id": "nonexistent"}
        )
        
        assert "error" in result

    def test_handle_search(self):
        """Test handling search tool call."""
        mock_engine = MagicMock()
        mock_engine.search.return_value = [
            MagicMock(to_dict=lambda: {"id": "1", "content": "Result 1"}),
            MagicMock(to_dict=lambda: {"id": "2", "content": "Result 2"})
        ]
        
        server = MCPServer(mock_engine)
        
        result = server.handle_tool_call(
            "memory.search",
            {"query": "test"}
        )
        
        assert "memories" in result
        assert len(result["memories"]) == 2

    def test_handle_update(self):
        """Test handling update tool call."""
        mock_engine = MagicMock()
        mock_memory = MagicMock()
        mock_memory.to_dict.return_value = {"id": "123", "content": "Updated"}
        mock_engine.update.return_value = mock_memory
        
        server = MCPServer(mock_engine)
        
        result = server.handle_tool_call(
            "memory.update",
            {"id": "123", "content": "Updated"}
        )
        
        assert "memory" in result
        mock_engine.update.assert_called_once()

    def test_handle_delete(self):
        """Test handling delete tool call."""
        mock_engine = MagicMock()
        mock_engine.delete.return_value = True
        
        server = MCPServer(mock_engine)
        
        result = server.handle_tool_call(
            "memory.delete",
            {"id": "123"}
        )
        
        assert result["success"] is True
        mock_engine.delete.assert_called_once_with("123")

    def test_handle_list(self):
        """Test handling list tool call."""
        mock_engine = MagicMock()
        mock_engine.list_memories.return_value = [
            MagicMock(to_dict=lambda: {"id": "1", "content": "Memory 1"}),
            MagicMock(to_dict=lambda: {"id": "2", "content": "Memory 2"})
        ]
        
        server = MCPServer(mock_engine)
        
        result = server.handle_tool_call(
            "memory.list",
            {"limit": 10}
        )
        
        assert "memories" in result
        assert len(result["memories"]) == 2

    def test_handle_health(self):
        """Test handling health tool call."""
        mock_engine = MagicMock()
        mock_engine.count.return_value = 42
        
        server = MCPServer(mock_engine)
        
        result = server.handle_tool_call(
            "memory.health",
            {}
        )
        
        assert "status" in result
        assert result["status"] == "healthy"

    def test_handle_stats(self):
        """Test handling stats tool call."""
        mock_engine = MagicMock()
        mock_engine.count.return_value = 100
        
        server = MCPServer(mock_engine)
        
        result = server.handle_tool_call(
            "memory.stats",
            {}
        )
        
        assert "total_memories" in result

    def test_handle_unknown_tool(self):
        """Test handling unknown tool call."""
        mock_engine = MagicMock()
        server = MCPServer(mock_engine)
        
        result = server.handle_tool_call(
            "unknown.tool",
            {}
        )
        
        assert "error" in result

    def test_handle_missing_required_param(self):
        """Test handling tool call with missing required parameter."""
        mock_engine = MagicMock()
        server = MCPServer(mock_engine)
        
        result = server.handle_tool_call(
            "memory.save",
            {}  # Missing content
        )
        
        assert "error" in result
