"""Memory engine for Memory MCP Server."""

import logging
import uuid
from datetime import datetime, timezone
from typing import Dict, List, Optional, Set

from memory_mcp.models import Memory, Confidence, Source
from memory_mcp.storage.redis_backend import RedisBackend
from memory_mcp.storage.index import IndexManager

logger = logging.getLogger(__name__)

# Common stop words to filter
STOP_WORDS = {
    "a", "an", "the", "is", "are", "was", "were", "be", "been", "being",
    "have", "has", "had", "do", "does", "did", "will", "would", "could",
    "should", "may", "might", "shall", "can", "need", "dare", "ought",
    "used", "to", "of", "in", "for", "on", "with", "at", "by", "from",
    "as", "into", "through", "during", "before", "after", "above", "below",
    "between", "out", "off", "over", "under", "again", "further", "then",
    "once", "here", "there", "when", "where", "why", "how", "all", "both",
    "each", "few", "more", "most", "other", "some", "such", "no", "nor",
    "not", "only", "own", "same", "so", "than", "too", "very", "just",
    "and", "but", "or", "if", "while", "he", "she", "it", "they", "them",
    "his", "her", "its", "their", "this", "that", "these", "those", "i",
    "me", "my", "we", "us", "our", "you", "your"
}


class MemoryEngine:
    """Core memory engine with CRUD operations and indexing."""

    def __init__(self, backend: RedisBackend, index: IndexManager):
        """Initialize memory engine.
        
        Args:
            backend: Redis storage backend
            index: Index manager
        """
        self._backend = backend
        self._index = index

    def generate_id(self) -> str:
        """Generate a unique memory ID."""
        return f"mem_{uuid.uuid4().hex[:12]}"

    def extract_keywords(self, content: str) -> List[str]:
        """Extract keywords from content.
        
        Args:
            content: Text content
            
        Returns:
            List of keywords (filtered, lowercase)
        """
        # Simple tokenization
        words = content.lower().split()
        
        # Remove punctuation and filter stop words
        keywords = []
        for word in words:
            # Remove common punctuation
            cleaned = word.strip(".,;:!?\"'()[]{}")
            if cleaned and cleaned not in STOP_WORDS and len(cleaned) > 1:
                keywords.append(cleaned)
        
        return keywords

    def save(self, memory: Memory) -> bool:
        """Save a memory with indexing.
        
        Args:
            memory: Memory to save
            
        Returns:
            True if successful
        """
        # Set timestamps
        now = datetime.now(timezone.utc)
        memory.created_at = now
        memory.updated_at = now
        
        # Save to backend
        success = self._backend.save(memory)
        if not success:
            return False
        
        # Update indexes
        for tag in memory.tags:
            self._index.add_tag(tag, memory.id)
        
        if memory.agent:
            self._index.add_agent(memory.agent, memory.id)
        
        # Extract and index keywords
        keywords = self.extract_keywords(memory.content)
        for keyword in keywords:
            self._index.add_keyword(keyword, memory.id)
        
        # Add to time index
        self._index.add_time(memory.id, now.timestamp())
        
        logger.info(f"Saved memory {memory.id} with {len(keywords)} keywords")
        return True

    def get(self, memory_id: str) -> Optional[Memory]:
        """Get a memory by ID.
        
        Args:
            memory_id: Memory ID
            
        Returns:
            Memory if found, None otherwise
        """
        return self._backend.get(memory_id)

    def update(
        self,
        memory_id: str,
        updates: Dict
    ) -> Optional[Memory]:
        """Update a memory.
        
        Args:
            memory_id: Memory ID
            updates: Dictionary of fields to update
            
        Returns:
            Updated memory if found, None otherwise
        """
        # Get existing memory
        memory = self._backend.get(memory_id)
        if memory is None:
            return None
        
        # Remove old indexes
        keywords = self.extract_keywords(memory.content)
        self._index.remove_memory(
            memory_id,
            tags=memory.tags,
            agent=memory.agent,
            keywords=keywords
        )
        
        # Apply updates
        if "content" in updates:
            memory.content = updates["content"]
        if "tags" in updates:
            memory.tags = updates["tags"]
        if "confidence" in updates:
            memory.confidence = Confidence(updates["confidence"])
        if "metadata" in updates:
            memory.metadata.update(updates["metadata"])
        
        # Update version and timestamp
        memory.version += 1
        memory.updated_at = datetime.now(timezone.utc)
        
        # Save updated memory
        success = self._backend.save(memory)
        if not success:
            return None
        
        # Update indexes with new values
        for tag in memory.tags:
            self._index.add_tag(tag, memory.id)
        
        if memory.agent:
            self._index.add_agent(memory.agent, memory.id)
        
        new_keywords = self.extract_keywords(memory.content)
        for keyword in new_keywords:
            self._index.add_keyword(keyword, memory.id)
        
        logger.info(f"Updated memory {memory_id} to version {memory.version}")
        return memory

    def delete(self, memory_id: str) -> bool:
        """Delete a memory.
        
        Args:
            memory_id: Memory ID
            
        Returns:
            True if deleted, False if not found
        """
        # Get memory to remove indexes
        memory = self._backend.get(memory_id)
        if memory is None:
            return False
        
        # Remove from backend
        success = self._backend.delete(memory_id)
        if not success:
            return False
        
        # Remove from indexes
        keywords = self.extract_keywords(memory.content)
        self._index.remove_memory(
            memory_id,
            tags=memory.tags,
            agent=memory.agent,
            keywords=keywords
        )
        
        logger.info(f"Deleted memory {memory_id}")
        return True

    def list_memories(
        self,
        limit: int = 100,
        offset: int = 0
    ) -> List[Memory]:
        """List memories.
        
        Args:
            limit: Maximum number of memories to return
            offset: Number of memories to skip
            
        Returns:
            List of memories
        """
        return self._backend.list_memories(limit=limit, offset=offset)

    def count(self) -> int:
        """Count total memories.
        
        Returns:
            Number of memories
        """
        return self._backend.count()

    def search_by_tags(self, tags: List[str]) -> Set[str]:
        """Search memories by tags.
        
        Args:
            tags: List of tags to search for
            
        Returns:
            Set of memory IDs
        """
        return self._index.search(tags=tags)

    def search_by_keywords(self, keywords: List[str]) -> Set[str]:
        """Search memories by keywords.
        
        Args:
            keywords: List of keywords to search for
            
        Returns:
            Set of memory IDs
        """
        return self._index.search(keywords=keywords)

    def search(
        self,
        query: Optional[str] = None,
        tags: Optional[List[str]] = None,
        agent: Optional[str] = None,
        limit: int = 10
    ) -> List[Memory]:
        """Search memories.
        
        Args:
            query: Search query (searches content)
            tags: Tags to filter by
            agent: Agent to filter by
            limit: Maximum results
            
        Returns:
            List of matching memories
        """
        # Get candidate IDs from indexes
        candidate_ids = None
        
        if tags:
            tag_ids = self._index.search(tags=tags)
            candidate_ids = tag_ids if candidate_ids is None else candidate_ids.intersection(tag_ids)
        
        if agent:
            agent_ids = self._index.search(agent=agent)
            candidate_ids = agent_ids if candidate_ids is None else candidate_ids.intersection(agent_ids)
        
        if query:
            keywords = self.extract_keywords(query)
            if keywords:
                keyword_ids = self._index.search(keywords=keywords)
                candidate_ids = keyword_ids if candidate_ids is None else candidate_ids.intersection(keyword_ids)
        
        # If no search criteria, return latest memories
        if candidate_ids is None:
            return self.list_memories(limit=limit)
        
        # Fetch memories and filter by query
        results = []
        for memory_id in candidate_ids:
            memory = self._backend.get(memory_id)
            if memory is None:
                continue
            
            # If query provided, check content contains query
            if query and query.lower() not in memory.content.lower():
                continue
            
            results.append(memory)
            
            if len(results) >= limit:
                break
        
        return results
