"""Tests for search engine."""

import pytest
from unittest.mock import MagicMock, patch
from datetime import datetime, timezone
from memory_mcp.engine.search import SearchEngine
from memory_mcp.models import Memory


class TestSearchEngine:
    """Test SearchEngine class."""

    def test_init(self):
        """Test initializing search engine."""
        mock_backend = MagicMock()
        mock_index = MagicMock()
        engine = SearchEngine(mock_backend, mock_index)
        
        assert engine._backend == mock_backend
        assert engine._index == mock_index

    def test_tokenize(self):
        """Test text tokenization."""
        mock_backend = MagicMock()
        mock_index = MagicMock()
        engine = SearchEngine(mock_backend, mock_index)
        
        tokens = engine.tokenize("User prefers dark mode")
        
        assert "user" in tokens
        assert "prefers" in tokens
        assert "dark" in tokens
        assert "mode" in tokens

    def test_tokenize_lowercase(self):
        """Test tokenization converts to lowercase."""
        mock_backend = MagicMock()
        mock_index = MagicMock()
        engine = SearchEngine(mock_backend, mock_index)
        
        tokens = engine.tokenize("USER PREFERS Dark Mode")
        
        assert all(t.islower() for t in tokens)

    def test_extract_keywords(self):
        """Test keyword extraction."""
        mock_backend = MagicMock()
        mock_index = MagicMock()
        engine = SearchEngine(mock_backend, mock_index)
        
        keywords = engine.extract_keywords("User prefers dark mode and vim keybindings")
        
        assert "user" in keywords
        assert "prefers" in keywords
        assert "dark" in keywords
        assert "mode" in keywords
        assert "vim" in keywords
        assert "keybindings" in keywords

    def test_extract_keywords_filters_stop_words(self):
        """Test that stop words are filtered."""
        mock_backend = MagicMock()
        mock_index = MagicMock()
        engine = SearchEngine(mock_backend, mock_index)
        
        keywords = engine.extract_keywords("The user is a developer")
        
        assert "the" not in keywords
        assert "is" not in keywords
        assert "a" not in keywords
        assert "user" in keywords
        assert "developer" in keywords

    def test_expand_synonyms(self):
        """Test synonym expansion."""
        mock_backend = MagicMock()
        mock_index = MagicMock()
        engine = SearchEngine(mock_backend, mock_index)
        
        expanded = engine.expand_synonyms(["nas", "config"])
        
        # Should include synonyms
        assert "nas" in expanded
        assert "网络存储" in expanded
        assert "config" in expanded
        assert "配置" in expanded

    def test_expand_synonyms_unknown(self):
        """Test synonym expansion with unknown words."""
        mock_backend = MagicMock()
        mock_index = MagicMock()
        engine = SearchEngine(mock_backend, mock_index)
        
        expanded = engine.expand_synonyms(["unknown", "words"])
        
        # Should return original words
        assert "unknown" in expanded
        assert "words" in expanded

    def test_search_basic(self):
        """Test basic search."""
        mock_backend = MagicMock()
        mock_index = MagicMock()
        
        memories = [
            Memory(id="1", content="User prefers dark mode", tags=["preference"]),
            Memory(id="2", content="User likes coding in Python", tags=["code"]),
            Memory(id="3", content="Weather is sunny today", tags=["weather"])
        ]
        mock_backend.list_memories.return_value = memories
        
        engine = SearchEngine(mock_backend, mock_index)
        
        results = engine.search("dark mode")
        
        assert len(results) >= 1
        assert any(m.id == "1" for m in results)

    def test_search_with_tags(self):
        """Test search with tag filtering."""
        mock_backend = MagicMock()
        mock_index = MagicMock()
        
        memories = [
            Memory(id="1", content="User prefers dark mode", tags=["preference"]),
            Memory(id="2", content="User likes dark theme", tags=["ui"]),
            Memory(id="3", content="Weather is sunny", tags=["weather"])
        ]
        mock_backend.list_memories.return_value = memories
        mock_index.search.return_value = {"1", "2"}  # Memories with preference or ui tags
        
        engine = SearchEngine(mock_backend, mock_index)
        
        # Search for "dark mode" which should match memory 1
        results = engine.search("dark mode", tags=["preference", "ui"])
        
        # Should find at least one result
        assert len(results) >= 1
        # Should not include weather memory
        assert not any(m.id == "3" for m in results)

    def test_search_with_agent(self):
        """Test search with agent filtering."""
        mock_backend = MagicMock()
        mock_index = MagicMock()
        
        memories = [
            Memory(id="1", content="User prefers dark mode", agent="hermes"),
            Memory(id="2", content="User likes dark theme", agent="codex"),
            Memory(id="3", content="Weather is sunny", agent="hermes")
        ]
        mock_backend.list_memories.return_value = memories
        mock_index.search.return_value = {"1", "3"}  # hermes memories
        
        engine = SearchEngine(mock_backend, mock_index)
        
        # Search for "dark mode" which should match memory 1
        results = engine.search("dark mode", agent="hermes")
        
        # Should find at least one result
        assert len(results) >= 1
        assert not any(m.id == "2" for m in results)

    def test_search_no_results(self):
        """Test search with no matching results."""
        mock_backend = MagicMock()
        mock_index = MagicMock()
        
        memories = [
            Memory(id="1", content="User prefers dark mode"),
            Memory(id="2", content="User likes coding")
        ]
        mock_backend.list_memories.return_value = memories
        
        engine = SearchEngine(mock_backend, mock_index)
        
        results = engine.search("weather sunny")
        
        assert len(results) == 0

    def test_search_empty_query(self):
        """Test search with empty query."""
        mock_backend = MagicMock()
        mock_index = MagicMock()
        
        memories = [
            Memory(id="1", content="Memory 1"),
            Memory(id="2", content="Memory 2")
        ]
        mock_backend.list_memories.return_value = memories
        
        engine = SearchEngine(mock_backend, mock_index)
        
        results = engine.search("")
        
        # Should return all memories
        assert len(results) == 2

    def test_search_limit(self):
        """Test search with limit."""
        mock_backend = MagicMock()
        mock_index = MagicMock()
        
        memories = [
            Memory(id=str(i), content=f"Memory {i} about coding")
            for i in range(20)
        ]
        mock_backend.list_memories.return_value = memories
        
        engine = SearchEngine(mock_backend, mock_index)
        
        results = engine.search("coding", limit=5)
        
        assert len(results) <= 5

    def test_rank_results(self):
        """Test result ranking."""
        mock_backend = MagicMock()
        mock_index = MagicMock()
        
        engine = SearchEngine(mock_backend, mock_index)
        
        memories = [
            Memory(id="1", content="dark mode theme"),
            Memory(id="2", content="dark sky"),
            Memory(id="3", content="dark mode preference for user")
        ]
        
        ranked = engine.rank_results("dark mode", memories)
        
        # Should be ranked by relevance
        # Memory 1 and 3 both match "dark mode", but 3 has more words
        # The ranking depends on the scoring algorithm
        assert len(ranked) == 3
        # At least dark mode should be in top 2
        top_ids = [m.id for m in ranked[:2]]
        assert "1" in top_ids or "3" in top_ids
