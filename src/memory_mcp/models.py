"""Data models for Memory MCP Server."""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List


class Confidence(str, Enum):
    """Confidence level for memories."""
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class Source(str, Enum):
    """Source of the memory."""
    USER = "user"
    SCRIPT = "script"
    INFERRED = "inferred"
    SYSTEM = "system"


@dataclass
class Memory:
    """Memory entry data model."""
    id: str
    content: str
    tags: List[str] = field(default_factory=list)
    agent: str = ""
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    version: int = 1
    confidence: Confidence = Confidence.HIGH
    source: Source = Source.USER
    links: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Serialize memory to dictionary."""
        return {
            "id": self.id,
            "content": self.content,
            "tags": self.tags,
            "agent": self.agent,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "version": self.version,
            "confidence": self.confidence.value,
            "source": self.source.value,
            "links": self.links,
            "metadata": self.metadata
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Memory":
        """Deserialize memory from dictionary."""
        return cls(
            id=data["id"],
            content=data["content"],
            tags=data.get("tags", []),
            agent=data.get("agent", ""),
            created_at=datetime.fromisoformat(data["created_at"]),
            updated_at=datetime.fromisoformat(data["updated_at"]),
            version=data.get("version", 1),
            confidence=Confidence(data.get("confidence", "high")),
            source=Source(data.get("source", "user")),
            links=data.get("links", []),
            metadata=data.get("metadata", {})
        )
