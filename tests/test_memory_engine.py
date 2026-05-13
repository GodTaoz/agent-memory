"""Tests for memory engine."""

import pytest
from unittest.mock import MagicMock, patch
from datetime import datetime, timezone
from memory_mcp.engine.memory import MemoryEngine
from memory_mcp.models import Memory, Confidence, Source


class TestMemoryEngine:
    """Test MemoryEngine class."""

    def test_init(self):
        """Test initializing memory engine."""
        mock_backend = MagicMock()
        mock_index = MagicMock()
        engine = MemoryEngine(mock_backend, mock_index)
        
        assert engine._backend == mock_backend
        assert engine._index == mock_index

    def test_save_memory(self):
        """Test saving a memory."""
        mock_backend = MagicMock()
        mock_backend.save.return_value = True
        mock_index = MagicMock()
        
        engine = MemoryEngine(mock_backend, mock_index)
        
        memory = Memory(
            id="test-123",
            content="User prefers dark mode",
            tags=["preference", "ui"],
            agent="hermes"
        )
        
        result = engine.save(memory)
        
        assert result is True
        mock_backend.save.assert_called_once_with(memory)
        
        # Verify indexes were updated
        mock_index.add_tag.assert_any_call("preference", "test-123")
        mock_index.add_tag.assert_any_call("ui", "test-123")
        mock_index.add_agent.assert_called_once_with("hermes", "test-123")
        mock_index.add_time.assert_called_once()

    def test_get_memory(self):
        """Test getting a memory by ID."""
        mock_backend = MagicMock()
        memory = Memory(id="test-123", content="Test content")
        mock_backend.get.return_value = memory
        mock_index = MagicMock()
        
        engine = MemoryEngine(mock_backend, mock_index)
        
        result = engine.get("test-123")
        
        assert result == memory
        mock_backend.get.assert_called_once_with("test-123")

    def test_get_nonexistent_memory(self):
        """Test getting a non-existent memory returns None."""
        mock_backend = MagicMock()
        mock_backend.get.return_value = None
        mock_index = MagicMock()
        
        engine = MemoryEngine(mock_backend, mock_index)
        
        result = engine.get("nonexistent")
        
        assert result is None

    def test_delete_memory(self):
        """Test deleting a memory."""
        mock_backend = MagicMock()
        memory = Memory(
            id="test-123",
            content="Test content",
            tags=["test"],
            agent="hermes"
        )
        mock_backend.get.return_value = memory
        mock_backend.delete.return_value = True
        mock_index = MagicMock()
        
        engine = MemoryEngine(mock_backend, mock_index)
        
        result = engine.delete("test-123")
        
        assert result is True
        mock_backend.delete.assert_called_once_with("test-123")
        # Keywords are extracted from content
        mock_index.remove_memory.assert_called_once_with(
            "test-123",
            tags=["test"],
            agent="hermes",
            keywords=["test", "content"]
        )

    def test_delete_nonexistent_memory(self):
        """Test deleting a non-existent memory returns False."""
        mock_backend = MagicMock()
        mock_backend.get.return_value = None
        mock_index = MagicMock()
        
        engine = MemoryEngine(mock_backend, mock_index)
        
        result = engine.delete("nonexistent")
        
        assert result is False

    def test_update_memory(self):
        """Test updating a memory."""
        mock_backend = MagicMock()
        existing = Memory(
            id="test-123",
            content="Old content",
            tags=["old"],
            agent="hermes",
            version=1
        )
        mock_backend.get.return_value = existing
        mock_backend.save.return_value = True
        mock_index = MagicMock()
        
        engine = MemoryEngine(mock_backend, mock_index)
        
        updates = {
            "content": "New content",
            "tags": ["new", "updated"]
        }
        
        result = engine.update("test-123", updates)
        
        assert result is not None
        assert result.content == "New content"
        assert result.tags == ["new", "updated"]
        assert result.version == 2  # Version incremented
        
        # Verify old indexes were removed and new ones added
        mock_index.remove_memory.assert_called_once()
        mock_index.add_tag.assert_any_call("new", "test-123")
        mock_index.add_tag.assert_any_call("updated", "test-123")

    def test_update_nonexistent_memory(self):
        """Test updating a non-existent memory returns None."""
        mock_backend = MagicMock()
        mock_backend.get.return_value = None
        mock_index = MagicMock()
        
        engine = MemoryEngine(mock_backend, mock_index)
        
        result = engine.update("nonexistent", {"content": "New"})
        
        assert result is None

    def test_list_memories(self):
        """Test listing memories."""
        mock_backend = MagicMock()
        memories = [
            Memory(id="1", content="Content 1"),
            Memory(id="2", content="Content 2")
        ]
        mock_backend.list_memories.return_value = memories
        mock_index = MagicMock()
        
        engine = MemoryEngine(mock_backend, mock_index)
        
        result = engine.list_memories(limit=10, offset=0)
        
        assert len(result) == 2
        mock_backend.list_memories.assert_called_once_with(limit=10, offset=0)

    def test_count_memories(self):
        """Test counting memories."""
        mock_backend = MagicMock()
        mock_backend.count.return_value = 42
        mock_index = MagicMock()
        
        engine = MemoryEngine(mock_backend, mock_index)
        
        result = engine.count()
        
        assert result == 42

    def test_extract_keywords(self):
        """Test extracting keywords from content."""
        mock_backend = MagicMock()
        mock_index = MagicMock()
        
        engine = MemoryEngine(mock_backend, mock_index)
        
        keywords = engine.extract_keywords("User prefers dark mode and vim keybindings")
        
        assert "user" in keywords
        assert "prefers" in keywords
        assert "dark" in keywords
        assert "mode" in keywords
        assert "vim" in keywords
        assert "keybindings" in keywords

    def test_extract_keywords_filters_stop_words(self):
        """Test that stop words are filtered from keywords."""
        mock_backend = MagicMock()
        mock_index = MagicMock()
        
        engine = MemoryEngine(mock_backend, mock_index)
        
        keywords = engine.extract_keywords("The user is a developer")
        
        assert "the" not in keywords
        assert "is" not in keywords
        assert "a" not in keywords
        assert "user" in keywords
        assert "developer" in keywords
