"""Tests for evolution engine."""

import pytest
from unittest.mock import MagicMock, patch
from datetime import datetime, timezone
from memory_mcp.engine.evolution import EvolutionEngine
from memory_mcp.models import Memory, Confidence, Source


class TestEvolutionEngine:
    """Test EvolutionEngine class."""

    def test_init(self):
        """Test initializing evolution engine."""
        mock_backend = MagicMock()
        engine = EvolutionEngine(mock_backend, similarity_threshold=0.3)
        
        assert engine._backend == mock_backend
        assert engine.similarity_threshold == 0.3

    def test_calculate_similarity_identical(self):
        """Test similarity of identical texts."""
        mock_backend = MagicMock()
        engine = EvolutionEngine(mock_backend)
        
        similarity = engine.calculate_similarity(
            "User prefers dark mode",
            "User prefers dark mode"
        )
        
        assert similarity == 1.0

    def test_calculate_similarity_similar(self):
        """Test similarity of similar texts."""
        mock_backend = MagicMock()
        engine = EvolutionEngine(mock_backend)
        
        similarity = engine.calculate_similarity(
            "User prefers dark mode",
            "User likes dark mode theme"
        )
        
        # Similar texts should have similarity >= 0.5
        assert similarity >= 0.5

    def test_calculate_similarity_different(self):
        """Test similarity of different texts."""
        mock_backend = MagicMock()
        engine = EvolutionEngine(mock_backend)
        
        similarity = engine.calculate_similarity(
            "User prefers dark mode",
            "The weather is sunny today"
        )
        
        assert similarity < 0.3

    def test_calculate_similarity_empty(self):
        """Test similarity with empty text."""
        mock_backend = MagicMock()
        engine = EvolutionEngine(mock_backend)
        
        similarity = engine.calculate_similarity("", "User prefers dark mode")
        
        assert similarity == 0.0

    def test_find_similar_memories(self):
        """Test finding similar memories."""
        mock_backend = MagicMock()
        
        # Setup existing memories
        existing = [
            Memory(
                id="mem-1",
                content="User prefers dark mode",
                tags=["preference", "ui"]
            ),
            Memory(
                id="mem-2",
                content="User likes coding in Python",
                tags=["preference", "code"]
            ),
            Memory(
                id="mem-3",
                content="Weather is sunny today",
                tags=["weather"]
            )
        ]
        mock_backend.list_memories.return_value = existing
        
        engine = EvolutionEngine(mock_backend, similarity_threshold=0.3)
        
        # Search for similar to "User likes dark theme"
        similar = engine.find_similar("User likes dark theme")
        
        # Should find mem-1 as similar
        assert len(similar) >= 1
        assert any(m.id == "mem-1" for m in similar)

    def test_find_similar_no_match(self):
        """Test finding similar when no match exists."""
        mock_backend = MagicMock()
        
        existing = [
            Memory(
                id="mem-1",
                content="User prefers dark mode",
                tags=["preference"]
            )
        ]
        mock_backend.list_memories.return_value = existing
        
        engine = EvolutionEngine(mock_backend, similarity_threshold=0.8)
        
        # Search for very different content
        similar = engine.find_similar("The weather is sunny")
        
        assert len(similar) == 0

    def test_merge_memories(self):
        """Test merging two memories."""
        mock_backend = MagicMock()
        engine = EvolutionEngine(mock_backend)
        
        old = Memory(
            id="mem-old",
            content="User prefers dark mode",
            tags=["preference", "ui"],
            agent="hermes",
            version=1,
            created_at=datetime(2026, 1, 1, tzinfo=timezone.utc)
        )
        
        new = Memory(
            id="mem-new",
            content="User likes dark mode and vim keybindings",
            tags=["preference", "editor"],
            agent="hermes"
        )
        
        merged = engine.merge(old, new)
        
        # Should keep old ID and created_at
        assert merged.id == "mem-old"
        assert merged.created_at == old.created_at
        
        # Should use new content
        assert merged.content == new.content
        
        # Should merge tags
        assert "preference" in merged.tags
        assert "ui" in merged.tags
        assert "editor" in merged.tags
        
        # Should increment version
        assert merged.version == 2
        
        # Should store old content in metadata
        assert "previous_content" in merged.metadata
        assert merged.metadata["previous_content"] == old.content

    def test_evolve_with_similar_existing(self):
        """Test evolving when similar memory exists."""
        mock_backend = MagicMock()
        
        existing = Memory(
            id="mem-existing",
            content="User prefers dark mode",
            tags=["preference"],
            version=1
        )
        mock_backend.list_memories.return_value = [existing]
        mock_backend.save.return_value = True
        mock_backend.delete.return_value = True
        
        engine = EvolutionEngine(mock_backend, similarity_threshold=0.3)
        
        new_memory = Memory(
            id="mem-new",
            content="User likes dark mode theme",
            tags=["ui"]
        )
        
        result = engine.evolve(new_memory)
        
        # Should return the merged memory
        assert result is not None
        assert result.id == "mem-existing"  # Keeps existing ID
        assert result.version == 2  # Version incremented
        
        # Should save merged memory
        mock_backend.save.assert_called_once()
        
        # Should delete new memory (since it was merged)
        mock_backend.delete.assert_called_once_with("mem-new")

    def test_evolve_without_similar(self):
        """Test evolving when no similar memory exists."""
        mock_backend = MagicMock()
        mock_backend.list_memories.return_value = []
        mock_backend.save.return_value = True
        
        engine = EvolutionEngine(mock_backend, similarity_threshold=0.3)
        
        new_memory = Memory(
            id="mem-new",
            content="Brand new information",
            tags=["new"]
        )
        
        result = engine.evolve(new_memory)
        
        # Should return the new memory as-is
        assert result is not None
        assert result.id == "mem-new"
        assert result.version == 1
        
        # Should save the new memory
        mock_backend.save.assert_called_once_with(new_memory)

    def test_evolve_preserves_confidence(self):
        """Test that evolution preserves higher confidence."""
        mock_backend = MagicMock()
        
        existing = Memory(
            id="mem-existing",
            content="User prefers dark mode",
            confidence=Confidence.HIGH,
            version=1
        )
        mock_backend.list_memories.return_value = [existing]
        mock_backend.save.return_value = True
        mock_backend.delete.return_value = True
        
        engine = EvolutionEngine(mock_backend, similarity_threshold=0.3)
        
        new_memory = Memory(
            id="mem-new",
            content="User likes dark mode",
            confidence=Confidence.LOW
        )
        
        result = engine.evolve(new_memory)
        
        # Should keep higher confidence
        assert result.confidence == Confidence.HIGH
