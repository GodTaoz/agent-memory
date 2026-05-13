"""Tests for Memory data model."""

import pytest
from datetime import datetime, timezone
from memory_mcp.models import Memory, Confidence, Source


class TestMemoryModel:
    """Test Memory data model."""

    def test_create_memory_with_defaults(self):
        """Test creating a memory with default values."""
        memory = Memory(
            id="test-123",
            content="Test memory content"
        )
        
        assert memory.id == "test-123"
        assert memory.content == "Test memory content"
        assert memory.tags == []
        assert memory.agent == ""
        assert memory.version == 1
        assert memory.confidence == Confidence.HIGH
        assert memory.source == Source.USER
        assert memory.links == []
        assert memory.metadata == {}

    def test_create_memory_with_all_fields(self):
        """Test creating a memory with all fields specified."""
        now = datetime.now(timezone.utc)
        memory = Memory(
            id="test-456",
            content="User prefers dark mode",
            tags=["preference", "ui"],
            agent="hermes",
            created_at=now,
            updated_at=now,
            version=2,
            confidence=Confidence.MEDIUM,
            source=Source.INFERRED,
            links=["other-memory-id"],
            metadata={"key": "value"}
        )
        
        assert memory.id == "test-456"
        assert memory.content == "User prefers dark mode"
        assert memory.tags == ["preference", "ui"]
        assert memory.agent == "hermes"
        assert memory.created_at == now
        assert memory.updated_at == now
        assert memory.version == 2
        assert memory.confidence == Confidence.MEDIUM
        assert memory.source == Source.INFERRED
        assert memory.links == ["other-memory-id"]
        assert memory.metadata == {"key": "value"}

    def test_memory_to_dict(self):
        """Test serializing memory to dictionary."""
        memory = Memory(
            id="test-789",
            content="Test content",
            tags=["test"],
            agent="codex"
        )
        
        data = memory.to_dict()
        
        assert data["id"] == "test-789"
        assert data["content"] == "Test content"
        assert data["tags"] == ["test"]
        assert data["agent"] == "codex"
        assert data["version"] == 1
        assert data["confidence"] == "high"
        assert data["source"] == "user"
        assert "created_at" in data
        assert "updated_at" in data

    def test_memory_from_dict(self):
        """Test deserializing memory from dictionary."""
        now = datetime.now(timezone.utc)
        data = {
            "id": "test-abc",
            "content": "Test content",
            "tags": ["test"],
            "agent": "hermes",
            "created_at": now.isoformat(),
            "updated_at": now.isoformat(),
            "version": 3,
            "confidence": "medium",
            "source": "inferred",
            "links": ["link1"],
            "metadata": {"foo": "bar"}
        }
        
        memory = Memory.from_dict(data)
        
        assert memory.id == "test-abc"
        assert memory.content == "Test content"
        assert memory.tags == ["test"]
        assert memory.agent == "hermes"
        assert memory.version == 3
        assert memory.confidence == Confidence.MEDIUM
        assert memory.source == Source.INFERRED
        assert memory.links == ["link1"]
        assert memory.metadata == {"foo": "bar"}

    def test_memory_roundtrip(self):
        """Test serialization and deserialization roundtrip."""
        original = Memory(
            id="roundtrip-test",
            content="Roundtrip test content",
            tags=["tag1", "tag2"],
            agent="claude-code",
            version=5,
            confidence=Confidence.LOW,
            source=Source.SCRIPT
        )
        
        data = original.to_dict()
        restored = Memory.from_dict(data)
        
        assert restored.id == original.id
        assert restored.content == original.content
        assert restored.tags == original.tags
        assert restored.agent == original.agent
        assert restored.version == original.version
        assert restored.confidence == original.confidence
        assert restored.source == original.source


class TestConfidenceEnum:
    """Test Confidence enum."""

    def test_confidence_values(self):
        """Test confidence enum values."""
        assert Confidence.HIGH == "high"
        assert Confidence.MEDIUM == "medium"
        assert Confidence.LOW == "low"

    def test_confidence_from_string(self):
        """Test creating confidence from string."""
        assert Confidence("high") == Confidence.HIGH
        assert Confidence("medium") == Confidence.MEDIUM
        assert Confidence("low") == Confidence.LOW


class TestSourceEnum:
    """Test Source enum."""

    def test_source_values(self):
        """Test source enum values."""
        assert Source.USER == "user"
        assert Source.SCRIPT == "script"
        assert Source.INFERRED == "inferred"
        assert Source.SYSTEM == "system"

    def test_source_from_string(self):
        """Test creating source from string."""
        assert Source("user") == Source.USER
        assert Source("script") == Source.SCRIPT
