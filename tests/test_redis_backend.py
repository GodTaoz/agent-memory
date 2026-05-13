"""Tests for Redis storage backend."""

import json
import pytest
from unittest.mock import MagicMock, patch
from memory_mcp.storage.redis_backend import RedisBackend
from memory_mcp.models import Memory


class TestRedisBackend:
    """Test RedisBackend class."""

    def test_init_with_default_config(self):
        """Test initializing Redis backend with default config."""
        backend = RedisBackend(host="localhost", port=6379)
        
        assert backend.host == "localhost"
        assert backend.port == 6379
        assert backend.key_prefix == "memory"

    def test_init_with_custom_config(self):
        """Test initializing Redis backend with custom config."""
        backend = RedisBackend(
            host="redis.example.com",
            port=6380,
            password="secret",
            db=1,
            key_prefix="mymemory"
        )
        
        assert backend.host == "redis.example.com"
        assert backend.port == 6380
        assert backend.password == "secret"
        assert backend.db == 1
        assert backend.key_prefix == "mymemory"

    @patch("redis.Redis")
    def test_connect(self, mock_redis):
        """Test connecting to Redis."""
        backend = RedisBackend()
        backend.connect()
        
        mock_redis.assert_called_once()
        mock_redis.return_value.ping.assert_called_once()

    @patch("redis.Redis")
    def test_save_memory(self, mock_redis):
        """Test saving a memory to Redis."""
        mock_client = MagicMock()
        mock_redis.return_value = mock_client
        
        backend = RedisBackend()
        backend.connect()
        
        memory = Memory(
            id="test-123",
            content="Test content",
            tags=["test"],
            agent="hermes"
        )
        
        result = backend.save(memory)
        
        assert result is True
        mock_client.set.assert_called_once()
        
        # Verify the key format
        call_args = mock_client.set.call_args
        assert call_args[0][0] == "memory:test-123"

    @patch("redis.Redis")
    def test_get_memory(self, mock_redis):
        """Test getting a memory from Redis."""
        mock_client = MagicMock()
        mock_redis.return_value = mock_client
        
        memory = Memory(
            id="test-456",
            content="Test content",
            tags=["test"],
            agent="codex"
        )
        mock_client.get.return_value = json.dumps(memory.to_dict())
        
        backend = RedisBackend()
        backend.connect()
        
        result = backend.get("test-456")
        
        assert result is not None
        assert result.id == "test-456"
        assert result.content == "Test content"
        assert result.agent == "codex"

    @patch("redis.Redis")
    def test_get_nonexistent_memory(self, mock_redis):
        """Test getting a non-existent memory returns None."""
        mock_client = MagicMock()
        mock_redis.return_value = mock_client
        mock_client.get.return_value = None
        
        backend = RedisBackend()
        backend.connect()
        
        result = backend.get("nonexistent")
        
        assert result is None

    @patch("redis.Redis")
    def test_delete_memory(self, mock_redis):
        """Test deleting a memory from Redis."""
        mock_client = MagicMock()
        mock_redis.return_value = mock_client
        mock_client.delete.return_value = 1
        
        backend = RedisBackend()
        backend.connect()
        
        result = backend.delete("test-789")
        
        assert result is True
        mock_client.delete.assert_called_once_with("memory:test-789")

    @patch("redis.Redis")
    def test_delete_nonexistent_memory(self, mock_redis):
        """Test deleting a non-existent memory returns False."""
        mock_client = MagicMock()
        mock_redis.return_value = mock_client
        mock_client.delete.return_value = 0
        
        backend = RedisBackend()
        backend.connect()
        
        result = backend.delete("nonexistent")
        
        assert result is False

    @patch("redis.Redis")
    def test_exists_memory(self, mock_redis):
        """Test checking if a memory exists."""
        mock_client = MagicMock()
        mock_redis.return_value = mock_client
        mock_client.exists.return_value = 1
        
        backend = RedisBackend()
        backend.connect()
        
        result = backend.exists("test-123")
        
        assert result is True
        mock_client.exists.assert_called_once_with("memory:test-123")

    @patch("redis.Redis")
    def test_count_memories(self, mock_redis):
        """Test counting memories."""
        mock_client = MagicMock()
        mock_redis.return_value = mock_client
        mock_client.keys.return_value = [
            "memory:1", "memory:2", "memory:3"
        ]
        
        backend = RedisBackend()
        backend.connect()
        
        result = backend.count()
        
        assert result == 3
        mock_client.keys.assert_called_once_with("memory:*")

    @patch("redis.Redis")
    def test_list_memories(self, mock_redis):
        """Test listing memories."""
        mock_client = MagicMock()
        mock_redis.return_value = mock_client
        
        memory1 = Memory(id="1", content="Content 1")
        memory2 = Memory(id="2", content="Content 2")
        
        mock_client.keys.return_value = ["memory:1", "memory:2"]
        mock_client.get.side_effect = [
            json.dumps(memory1.to_dict()),
            json.dumps(memory2.to_dict())
        ]
        
        backend = RedisBackend()
        backend.connect()
        
        result = backend.list_memories(limit=10)
        
        assert len(result) == 2
        assert result[0].id == "1"
        assert result[1].id == "2"
