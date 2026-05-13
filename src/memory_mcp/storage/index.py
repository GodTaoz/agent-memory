"""Index management for Memory MCP Server."""

import logging
from typing import List, Optional, Set

import redis

logger = logging.getLogger(__name__)


class IndexManager:
    """Manages indexes for fast memory lookup."""

    def __init__(self, client: redis.Redis, prefix: str = "memory"):
        """Initialize index manager.
        
        Args:
            client: Redis client
            prefix: Key prefix for indexes
        """
        self._client = client
        self.prefix = prefix

    def _tag_key(self, tag: str) -> str:
        """Get Redis key for a tag index."""
        return f"{self.prefix}:index:tag:{tag}"

    def _agent_key(self, agent: str) -> str:
        """Get Redis key for an agent index."""
        return f"{self.prefix}:index:agent:{agent}"

    def _keyword_key(self, keyword: str) -> str:
        """Get Redis key for a keyword index."""
        return f"{self.prefix}:index:keyword:{keyword}"

    def _time_key(self) -> str:
        """Get Redis key for time index."""
        return f"{self.prefix}:index:time"

    def add_tag(self, tag: str, memory_id: str) -> None:
        """Add a memory to a tag index.
        
        Args:
            tag: Tag name
            memory_id: Memory ID
        """
        key = self._tag_key(tag)
        self._client.sadd(key, memory_id)
        logger.debug(f"Added {memory_id} to tag index {tag}")

    def remove_tag(self, tag: str, memory_id: str) -> None:
        """Remove a memory from a tag index.
        
        Args:
            tag: Tag name
            memory_id: Memory ID
        """
        key = self._tag_key(tag)
        self._client.srem(key, memory_id)
        logger.debug(f"Removed {memory_id} from tag index {tag}")

    def get_by_tag(self, tag: str) -> Set[str]:
        """Get memory IDs by tag.
        
        Args:
            tag: Tag name
            
        Returns:
            Set of memory IDs
        """
        key = self._tag_key(tag)
        return self._client.smembers(key)

    def add_agent(self, agent: str, memory_id: str) -> None:
        """Add a memory to an agent index.
        
        Args:
            agent: Agent name
            memory_id: Memory ID
        """
        key = self._agent_key(agent)
        self._client.sadd(key, memory_id)
        logger.debug(f"Added {memory_id} to agent index {agent}")

    def remove_agent(self, agent: str, memory_id: str) -> None:
        """Remove a memory from an agent index.
        
        Args:
            agent: Agent name
            memory_id: Memory ID
        """
        key = self._agent_key(agent)
        self._client.srem(key, memory_id)
        logger.debug(f"Removed {memory_id} from agent index {agent}")

    def get_by_agent(self, agent: str) -> Set[str]:
        """Get memory IDs by agent.
        
        Args:
            agent: Agent name
            
        Returns:
            Set of memory IDs
        """
        key = self._agent_key(agent)
        return self._client.smembers(key)

    def add_keyword(self, keyword: str, memory_id: str) -> None:
        """Add a memory to a keyword index.
        
        Args:
            keyword: Keyword
            memory_id: Memory ID
        """
        key = self._keyword_key(keyword.lower())
        self._client.sadd(key, memory_id)
        logger.debug(f"Added {memory_id} to keyword index {keyword}")

    def remove_keyword(self, keyword: str, memory_id: str) -> None:
        """Remove a memory from a keyword index.
        
        Args:
            keyword: Keyword
            memory_id: Memory ID
        """
        key = self._keyword_key(keyword.lower())
        self._client.srem(key, memory_id)
        logger.debug(f"Removed {memory_id} from keyword index {keyword}")

    def get_by_keyword(self, keyword: str) -> Set[str]:
        """Get memory IDs by keyword.
        
        Args:
            keyword: Keyword
            
        Returns:
            Set of memory IDs
        """
        key = self._keyword_key(keyword.lower())
        return self._client.smembers(key)

    def add_time(self, memory_id: str, timestamp: float) -> None:
        """Add a memory to the time index.
        
        Args:
            memory_id: Memory ID
            timestamp: Unix timestamp
        """
        key = self._time_key()
        self._client.zadd(key, {memory_id: timestamp})
        logger.debug(f"Added {memory_id} to time index")

    def remove_time(self, memory_id: str) -> None:
        """Remove a memory from the time index.
        
        Args:
            memory_id: Memory ID
        """
        key = self._time_key()
        self._client.zrem(key, memory_id)
        logger.debug(f"Removed {memory_id} from time index")

    def get_by_time_range(
        self,
        start: float,
        end: float
    ) -> List[str]:
        """Get memory IDs by time range.
        
        Args:
            start: Start timestamp
            end: End timestamp
            
        Returns:
            List of memory IDs
        """
        key = self._time_key()
        return self._client.zrangebyscore(key, min=start, max=end)

    def remove_memory(
        self,
        memory_id: str,
        tags: Optional[List[str]] = None,
        agent: Optional[str] = None,
        keywords: Optional[List[str]] = None
    ) -> None:
        """Remove a memory from all indexes.
        
        Args:
            memory_id: Memory ID
            tags: Tags to remove from
            agent: Agent to remove from
            keywords: Keywords to remove from
        """
        if tags:
            for tag in tags:
                self.remove_tag(tag, memory_id)
        
        if agent:
            self.remove_agent(agent, memory_id)
        
        if keywords:
            for keyword in keywords:
                self.remove_keyword(keyword, memory_id)
        
        self.remove_time(memory_id)

    def search(
        self,
        tags: Optional[List[str]] = None,
        keywords: Optional[List[str]] = None,
        agent: Optional[str] = None
    ) -> Set[str]:
        """Search by tags, keywords, and agent.
        
        Args:
            tags: Tags to search for
            keywords: Keywords to search for
            agent: Agent to search for
            
        Returns:
            Set of memory IDs matching all criteria
        """
        sets = []
        
        if tags:
            for tag in tags:
                tag_ids = self.get_by_tag(tag)
                if tag_ids:
                    sets.append(tag_ids)
        
        if keywords:
            for keyword in keywords:
                keyword_ids = self.get_by_keyword(keyword)
                if keyword_ids:
                    sets.append(keyword_ids)
        
        if agent:
            agent_ids = self.get_by_agent(agent)
            if agent_ids:
                sets.append(agent_ids)
        
        if not sets:
            return set()
        
        # Return intersection of all sets
        result = sets[0]
        for s in sets[1:]:
            result = result.intersection(s)
        
        return result
