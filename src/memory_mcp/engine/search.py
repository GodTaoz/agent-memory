"""Search engine for Memory MCP Server.

This module provides advanced search capabilities including:
- Multi-level indexing (Key → Tag → Keyword)
- Synonym expansion
- Result ranking
"""

import logging
from typing import Dict, List, Optional, Set

from memory_mcp.models import Memory
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

# Synonym mappings for common terms
SYNONYMS: Dict[str, List[str]] = {
    "nas": ["网络存储", "samba", "存储服务"],
    "config": ["配置", "设置", "setting"],
    "email": ["邮箱", "邮件"],
    "memory": ["记忆", "memories"],
    "code": ["代码", "编码"],
    "ui": ["界面", "interface"],
    "preference": ["偏好", "喜好"],
    "theme": ["主题", "风格"],
}


class SearchEngine:
    """Advanced search engine with multi-level indexing and synonym expansion."""

    def __init__(self, backend: RedisBackend, index: IndexManager):
        """Initialize search engine.
        
        Args:
            backend: Redis storage backend
            index: Index manager
        """
        self._backend = backend
        self._index = index

    def tokenize(self, text: str) -> List[str]:
        """Tokenize text into words.
        
        Args:
            text: Input text
            
        Returns:
            List of lowercase tokens
        """
        return text.lower().split()

    def extract_keywords(self, content: str) -> List[str]:
        """Extract keywords from content.
        
        Args:
            content: Text content
            
        Returns:
            List of keywords (filtered, lowercase)
        """
        words = self.tokenize(content)
        
        # Filter stop words and short words
        keywords = [
            word.strip(".,;:!?\"'()[]{}")
            for word in words
        ]
        
        return [
            kw for kw in keywords
            if kw and kw not in STOP_WORDS and len(kw) > 1
        ]

    def expand_synonyms(self, keywords: List[str]) -> List[str]:
        """Expand keywords with synonyms.
        
        Args:
            keywords: Original keywords
            
        Returns:
            Expanded keywords including synonyms
        """
        expanded = set(keywords)
        
        for keyword in keywords:
            if keyword in SYNONYMS:
                expanded.update(SYNONYMS[keyword])
        
        return list(expanded)

    def rank_results(
        self,
        query: str,
        memories: List[Memory]
    ) -> List[Memory]:
        """Rank search results by relevance.
        
        Args:
            query: Original query
            memories: List of candidate memories
            
        Returns:
            Ranked list of memories
        """
        query_keywords = set(self.extract_keywords(query))
        
        def calculate_score(memory: Memory) -> float:
            """Calculate relevance score for a memory."""
            content_keywords = set(self.extract_keywords(memory.content))
            
            if not query_keywords or not content_keywords:
                return 0.0
            
            # Calculate keyword overlap
            intersection = query_keywords & content_keywords
            score = len(intersection) / len(query_keywords)
            
            # Bonus for exact substring match
            if query.lower() in memory.content.lower():
                score += 0.5
            
            return score
        
        # Sort by score (descending)
        return sorted(memories, key=calculate_score, reverse=True)

    def search(
        self,
        query: str = "",
        tags: Optional[List[str]] = None,
        agent: Optional[str] = None,
        limit: int = 10
    ) -> List[Memory]:
        """Search memories with multi-level indexing.
        
        Args:
            query: Search query
            tags: Tags to filter by
            agent: Agent to filter by
            limit: Maximum results
            
        Returns:
            List of matching memories
        """
        # Get all memories
        all_memories = self._backend.list_memories(limit=1000)
        
        # Filter by tags if provided
        if tags:
            tag_ids = self._index.search(tags=tags)
            all_memories = [m for m in all_memories if m.id in tag_ids]
        
        # Filter by agent if provided
        if agent:
            agent_ids = self._index.search(agent=agent)
            all_memories = [m for m in all_memories if m.id in agent_ids]
        
        # If no query, return all memories
        if not query:
            return all_memories[:limit]
        
        # Extract and expand keywords
        keywords = self.extract_keywords(query)
        expanded_keywords = self.expand_synonyms(keywords)
        
        # Filter by keyword presence
        results = []
        for memory in all_memories:
            content_lower = memory.content.lower()
            
            # Check if any keyword is in content
            if any(kw in content_lower for kw in expanded_keywords):
                results.append(memory)
        
        # Rank results
        ranked = self.rank_results(query, results)
        
        return ranked[:limit]

    def search_by_similarity(
        self,
        content: str,
        threshold: float = 0.3,
        limit: int = 10
    ) -> List[Memory]:
        """Search by content similarity.
        
        Args:
            content: Content to compare against
            threshold: Minimum similarity threshold
            limit: Maximum results
            
        Returns:
            List of similar memories
        """
        all_memories = self._backend.list_memories(limit=1000)
        
        # Calculate similarity for each memory
        similar = []
        for memory in all_memories:
            similarity = self._calculate_similarity(content, memory.content)
            if similarity >= threshold:
                similar.append((similarity, memory))
        
        # Sort by similarity (descending)
        similar.sort(key=lambda x: x[0], reverse=True)
        
        return [memory for _, memory in similar[:limit]]

    def _calculate_similarity(self, text1: str, text2: str) -> float:
        """Calculate similarity between two texts.
        
        Args:
            text1: First text
            text2: Second text
            
        Returns:
            Similarity score between 0.0 and 1.0
        """
        if not text1 or not text2:
            return 0.0
        
        words1 = set(self.tokenize(text1))
        words2 = set(self.tokenize(text2))
        
        if not words1 or not words2:
            return 0.0
        
        # Calculate Jaccard similarity
        intersection = words1 & words2
        union = words1 | words2
        
        return len(intersection) / len(union)
