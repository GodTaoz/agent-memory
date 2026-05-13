"""Tests for index management."""

import pytest
from unittest.mock import MagicMock, patch
from memory_mcp.storage.index import IndexManager


class TestIndexManager:
    """Test IndexManager class."""

    def test_init(self):
        """Test initializing index manager."""
        mock_client = MagicMock()
        manager = IndexManager(mock_client, prefix="memory")
        
        assert manager._client == mock_client
        assert manager.prefix == "memory"

    def test_add_tag_index(self):
        """Test adding a tag index entry."""
        mock_client = MagicMock()
        manager = IndexManager(mock_client, prefix="memory")
        
        manager.add_tag("tag1", "memory-123")
        
        mock_client.sadd.assert_called_once_with("memory:index:tag:tag1", "memory-123")

    def test_remove_tag_index(self):
        """Test removing a tag index entry."""
        mock_client = MagicMock()
        manager = IndexManager(mock_client, prefix="memory")
        
        manager.remove_tag("tag1", "memory-123")
        
        mock_client.srem.assert_called_once_with("memory:index:tag:tag1", "memory-123")

    def test_get_by_tag(self):
        """Test getting memory IDs by tag."""
        mock_client = MagicMock()
        mock_client.smembers.return_value = {"memory-1", "memory-2", "memory-3"}
        manager = IndexManager(mock_client, prefix="memory")
        
        result = manager.get_by_tag("tag1")
        
        assert result == {"memory-1", "memory-2", "memory-3"}
        mock_client.smembers.assert_called_once_with("memory:index:tag:tag1")

    def test_add_agent_index(self):
        """Test adding an agent index entry."""
        mock_client = MagicMock()
        manager = IndexManager(mock_client, prefix="memory")
        
        manager.add_agent("hermes", "memory-123")
        
        mock_client.sadd.assert_called_once_with("memory:index:agent:hermes", "memory-123")

    def test_get_by_agent(self):
        """Test getting memory IDs by agent."""
        mock_client = MagicMock()
        mock_client.smembers.return_value = {"memory-1", "memory-2"}
        manager = IndexManager(mock_client, prefix="memory")
        
        result = manager.get_by_agent("hermes")
        
        assert result == {"memory-1", "memory-2"}
        mock_client.smembers.assert_called_once_with("memory:index:agent:hermes")

    def test_add_keyword_index(self):
        """Test adding a keyword index entry."""
        mock_client = MagicMock()
        manager = IndexManager(mock_client, prefix="memory")
        
        manager.add_keyword("python", "memory-123")
        
        mock_client.sadd.assert_called_once_with("memory:index:keyword:python", "memory-123")

    def test_get_by_keyword(self):
        """Test getting memory IDs by keyword."""
        mock_client = MagicMock()
        mock_client.smembers.return_value = {"memory-1", "memory-3"}
        manager = IndexManager(mock_client, prefix="memory")
        
        result = manager.get_by_keyword("python")
        
        assert result == {"memory-1", "memory-3"}
        mock_client.smembers.assert_called_once_with("memory:index:keyword:python")

    def test_add_time_index(self):
        """Test adding a time index entry."""
        mock_client = MagicMock()
        manager = IndexManager(mock_client, prefix="memory")
        
        manager.add_time("memory-123", 1234567890.0)
        
        mock_client.zadd.assert_called_once_with(
            "memory:index:time",
            {"memory-123": 1234567890.0}
        )

    def test_get_by_time_range(self):
        """Test getting memory IDs by time range."""
        mock_client = MagicMock()
        mock_client.zrangebyscore.return_value = ["memory-1", "memory-2"]
        manager = IndexManager(mock_client, prefix="memory")
        
        result = manager.get_by_time_range(
            start=1234567890.0,
            end=1234567900.0
        )
        
        assert result == ["memory-1", "memory-2"]
        mock_client.zrangebyscore.assert_called_once_with(
            "memory:index:time",
            min=1234567890.0,
            max=1234567900.0
        )

    def test_remove_memory(self):
        """Test removing a memory from all indexes."""
        mock_client = MagicMock()
        manager = IndexManager(mock_client, prefix="memory")
        
        # Mock the index data
        mock_client.smembers.side_effect = [
            {"tag1", "tag2"},  # tags
            {"hermes"},  # agents
            {"python", "code"},  # keywords
        ]
        
        manager.remove_memory(
            "memory-123",
            tags=["tag1", "tag2"],
            agent="hermes",
            keywords=["python", "code"]
        )
        
        # Verify removals
        assert mock_client.srem.call_count == 5  # 2 tags + 1 agent + 2 keywords
        mock_client.zrem.assert_called_once_with("memory:index:time", "memory-123")

    def test_search_by_tags_and_keywords(self):
        """Test searching by multiple tags and keywords."""
        mock_client = MagicMock()
        manager = IndexManager(mock_client)
        
        # Mock tag results
        mock_client.smembers.side_effect = [
            {"memory-1", "memory-2", "memory-3"},  # tag1
            {"memory-2", "memory-3", "memory-4"},  # tag2
            {"memory-1", "memory-3", "memory-5"},  # keyword1
        ]
        
        result = manager.search(tags=["tag1", "tag2"], keywords=["keyword1"])
        
        # Should return intersection: {memory-3}
        assert result == {"memory-3"}
