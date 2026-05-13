"""Evolution engine for Memory MCP Server.

This module handles memory evolution - automatically merging similar memories
to avoid duplicates and maintain a clean memory store.
"""

import logging
from datetime import datetime, timezone
from typing import List, Optional, Set

from memory_mcp.models import Memory, Confidence
from memory_mcp.storage.redis_backend import RedisBackend

logger = logging.getLogger(__name__)


class EvolutionEngine:
    """Handles memory evolution through similarity detection and merging."""

    def __init__(
        self,
        backend: RedisBackend,
        similarity_threshold: float = 0.3
    ):
        """Initialize evolution engine.
        
        Args:
            backend: Redis storage backend
            similarity_threshold: Minimum similarity to consider memories as related
        """
        self._backend = backend
        self.similarity_threshold = similarity_threshold

    def tokenize(self, text: str) -> Set[str]:
        """Tokenize text into words.
        
        Args:
            text: Input text
            
        Returns:
            Set of lowercase words
        """
        return set(text.lower().split())

    def calculate_similarity(self, text1: str, text2: str) -> float:
        """Calculate similarity between two texts using word overlap.
        
        Args:
            text1: First text
            text2: Second text
            
        Returns:
            Similarity score between 0.0 and 1.0
        """
        if not text1 or not text2:
            return 0.0
        
        words1 = self.tokenize(text1)
        words2 = self.tokenize(text2)
        
        if not words1 or not words2:
            return 0.0
        
        # Calculate Jaccard similarity
        intersection = words1 & words2
        union = words1 | words2
        
        return len(intersection) / len(union)

    def find_similar(
        self,
        content: str,
        limit: int = 5
    ) -> List[Memory]:
        """Find memories similar to the given content.
        
        Args:
            content: Content to compare against
            limit: Maximum number of similar memories to return
            
        Returns:
            List of similar memories
        """
        all_memories = self._backend.list_memories(limit=1000)
        
        similar = []
        for memory in all_memories:
            similarity = self.calculate_similarity(content, memory.content)
            if similarity >= self.similarity_threshold:
                similar.append((similarity, memory))
        
        # Sort by similarity (descending)
        similar.sort(key=lambda x: x[0], reverse=True)
        
        return [memory for _, memory in similar[:limit]]

    def merge(self, old: Memory, new: Memory) -> Memory:
        """Merge two memories, keeping the best of both.
        
        Args:
            old: Existing memory
            new: New memory to merge with
            
        Returns:
            Merged memory
        """
        # Keep old ID and created_at
        merged_id = old.id
        created_at = old.created_at
        
        # Use new content (it's the latest information)
        content = new.content
        
        # Merge tags (union)
        tags = list(set(old.tags + new.tags))
        
        # Use higher confidence
        confidence = old.confidence
        if new.confidence == Confidence.HIGH:
            confidence = Confidence.HIGH
        elif new.confidence == Confidence.MEDIUM and old.confidence == Confidence.LOW:
            confidence = Confidence.MEDIUM
        
        # Increment version
        version = max(old.version, new.version) + 1
        
        # Store old content in metadata for history
        metadata = dict(old.metadata)
        metadata["previous_content"] = old.content
        metadata["merged_from"] = new.id
        metadata["merged_at"] = datetime.now(timezone.utc).isoformat()
        
        # Create merged memory
        merged = Memory(
            id=merged_id,
            content=content,
            tags=tags,
            agent=old.agent or new.agent,
            created_at=created_at,
            updated_at=datetime.now(timezone.utc),
            version=version,
            confidence=confidence,
            source=old.source,
            links=list(set(old.links + new.links)),
            metadata=metadata
        )
        
        return merged

    def evolve(self, memory: Memory) -> Optional[Memory]:
        """Evolve a memory - find similar and merge if found.
        
        Args:
            memory: New memory to evolve
            
        Returns:
            Merged memory if similar found, otherwise the original memory
        """
        # Find similar memories
        similar = self.find_similar(memory.content, limit=1)
        
        if similar:
            existing = similar[0]
            
            # Merge memories
            merged = self.merge(existing, memory)
            
            # Save merged memory
            self._backend.save(merged)
            
            # Delete the new memory (it was merged)
            if memory.id != existing.id:
                self._backend.delete(memory.id)
            
            logger.info(
                f"Evolved memory: merged '{memory.id}' into '{existing.id}' "
                f"(version {merged.version})"
            )
            
            return merged
        else:
            # No similar memory found, save as new
            self._backend.save(memory)
            logger.info(f"No similar memory found, saved new: '{memory.id}'")
            return memory

    def batch_evolve(self, memories: List[Memory]) -> List[Memory]:
        """Evolve a batch of memories.
        
        Args:
            memories: List of memories to evolve
            
        Returns:
            List of evolved memories
        """
        results = []
        for memory in memories:
            evolved = self.evolve(memory)
            if evolved:
                results.append(evolved)
        return results
