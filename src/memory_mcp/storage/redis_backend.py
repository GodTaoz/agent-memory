"""Redis storage backend for Memory MCP Server."""

import json
import logging
from typing import List, Optional

import redis

from memory_mcp.models import Memory

logger = logging.getLogger(__name__)


class RedisBackend:
    """Redis-based storage backend for memories."""

    def __init__(
        self,
        host: str = "localhost",
        port: int = 6379,
        password: str = "",
        db: int = 0,
        key_prefix: str = "memory"
    ):
        """Initialize Redis backend.
        
        Args:
            host: Redis host
            port: Redis port
            password: Redis password
            db: Redis database number
            key_prefix: Prefix for Redis keys
        """
        self.host = host
        self.port = port
        self.password = password
        self.db = db
        self.key_prefix = key_prefix
        self._client: Optional[redis.Redis] = None

    def connect(self) -> None:
        """Connect to Redis."""
        self._client = redis.Redis(
            host=self.host,
            port=self.port,
            password=self.password or None,
            db=self.db,
            decode_responses=True
        )
        # Test connection
        self._client.ping()
        logger.info(f"Connected to Redis at {self.host}:{self.port}")

    def disconnect(self) -> None:
        """Disconnect from Redis."""
        if self._client:
            self._client.close()
            self._client = None

    def _get_key(self, memory_id: str) -> str:
        """Get Redis key for a memory ID."""
        return f"{self.key_prefix}:{memory_id}"

    def _ensure_connected(self) -> redis.Redis:
        """Ensure Redis client is connected."""
        if self._client is None:
            raise RuntimeError("Not connected to Redis. Call connect() first.")
        return self._client

    def save(self, memory: Memory) -> bool:
        """Save a memory to Redis.
        
        Args:
            memory: Memory to save
            
        Returns:
            True if successful
        """
        client = self._ensure_connected()
        key = self._get_key(memory.id)
        data = json.dumps(memory.to_dict(), ensure_ascii=False)
        client.set(key, data)
        logger.debug(f"Saved memory {memory.id}")
        return True

    def get(self, memory_id: str) -> Optional[Memory]:
        """Get a memory from Redis.
        
        Args:
            memory_id: Memory ID
            
        Returns:
            Memory if found, None otherwise
        """
        client = self._ensure_connected()
        key = self._get_key(memory_id)
        data = client.get(key)
        
        if data is None:
            return None
        
        try:
            memory_dict = json.loads(data)
            return Memory.from_dict(memory_dict)
        except (json.JSONDecodeError, KeyError) as e:
            logger.error(f"Failed to parse memory {memory_id}: {e}")
            return None

    def delete(self, memory_id: str) -> bool:
        """Delete a memory from Redis.
        
        Args:
            memory_id: Memory ID
            
        Returns:
            True if deleted, False if not found
        """
        client = self._ensure_connected()
        key = self._get_key(memory_id)
        result = client.delete(key)
        return result > 0

    def exists(self, memory_id: str) -> bool:
        """Check if a memory exists in Redis.
        
        Args:
            memory_id: Memory ID
            
        Returns:
            True if exists
        """
        client = self._ensure_connected()
        key = self._get_key(memory_id)
        return client.exists(key) > 0

    def count(self) -> int:
        """Count total memories in Redis.
        
        Returns:
            Number of memories
        """
        client = self._ensure_connected()
        pattern = f"{self.key_prefix}:*"
        keys = client.keys(pattern)
        return len(keys)

    def list_memories(
        self,
        limit: int = 100,
        offset: int = 0
    ) -> List[Memory]:
        """List memories from Redis.
        
        Args:
            limit: Maximum number of memories to return
            offset: Number of memories to skip
            
        Returns:
            List of memories
        """
        client = self._ensure_connected()
        pattern = f"{self.key_prefix}:*"
        keys = client.keys(pattern)
        
        # Apply pagination
        paginated_keys = keys[offset:offset + limit]
        
        memories = []
        for key in paginated_keys:
            data = client.get(key)
            if data:
                try:
                    memory_dict = json.loads(data)
                    memories.append(Memory.from_dict(memory_dict))
                except (json.JSONDecodeError, KeyError) as e:
                    logger.error(f"Failed to parse memory from key {key}: {e}")
                    continue
        
        return memories

    def clear(self) -> int:
        """Clear all memories from Redis.
        
        Returns:
            Number of memories deleted
        """
        client = self._ensure_connected()
        pattern = f"{self.key_prefix}:*"
        keys = client.keys(pattern)
        
        if keys:
            return client.delete(*keys)
        return 0
