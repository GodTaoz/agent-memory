"""REST API for Memory MCP Server.

This module implements the REST API endpoints for memory operations.
"""

import logging
from typing import Any, Dict, List, Optional

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from memory_mcp.engine.memory import MemoryEngine
from memory_mcp.models import Memory

logger = logging.getLogger(__name__)


# Request/Response models
class MemoryCreate(BaseModel):
    """Request model for creating a memory."""
    content: str = Field(..., description="Memory content")
    tags: List[str] = Field(default_factory=list, description="Tags")
    agent: str = Field(default="", description="Agent name")
    confidence: str = Field(default="high", description="Confidence level")


class MemoryUpdate(BaseModel):
    """Request model for updating a memory."""
    content: Optional[str] = Field(None, description="New content")
    tags: Optional[List[str]] = Field(None, description="New tags")


class MemoryResponse(BaseModel):
    """Response model for a memory."""
    id: str
    content: str
    tags: List[str]
    agent: str
    created_at: str
    updated_at: str
    version: int
    confidence: str
    source: str
    links: List[str]
    metadata: Dict[str, Any]


class MemoryListResponse(BaseModel):
    """Response model for listing memories."""
    memories: List[MemoryResponse]
    total: int


class SuccessResponse(BaseModel):
    """Response model for success."""
    success: bool
    message: Optional[str] = None


def create_app(engine: MemoryEngine) -> FastAPI:
    """Create FastAPI application.
    
    Args:
        engine: Memory engine instance
        
    Returns:
        FastAPI application
    """
    app = FastAPI(
        title="Memory MCP Server",
        description="Universal Memory Service for AI Agents",
        version="0.1.0"
    )
    
    @app.get("/api/v1/health")
    async def health():
        """Health check endpoint."""
        count = engine.count()
        return {"status": "healthy", "total_memories": count}

    @app.get("/api/v1/stats")
    async def stats():
        """Statistics endpoint."""
        count = engine.count()
        return {"total_memories": count}

    @app.post("/api/v1/memories", response_model=MemoryResponse, status_code=201)
    async def create_memory(request: MemoryCreate):
        """Create a new memory."""
        memory = Memory(
            id=engine.generate_id(),
            content=request.content,
            tags=request.tags,
            agent=request.agent
        )
        
        success = engine.save(memory)
        if not success:
            raise HTTPException(status_code=500, detail="Failed to save memory")
        
        return memory.to_dict()

    @app.get("/api/v1/memories/{memory_id}", response_model=MemoryResponse)
    async def get_memory(memory_id: str):
        """Get a memory by ID."""
        memory = engine.get(memory_id)
        if memory is None:
            raise HTTPException(status_code=404, detail="Memory not found")
        
        return memory.to_dict()

    @app.put("/api/v1/memories/{memory_id}", response_model=MemoryResponse)
    async def update_memory(memory_id: str, request: MemoryUpdate):
        """Update an existing memory."""
        updates = {}
        if request.content is not None:
            updates["content"] = request.content
        if request.tags is not None:
            updates["tags"] = request.tags
        
        memory = engine.update(memory_id, updates)
        if memory is None:
            raise HTTPException(status_code=404, detail="Memory not found")
        
        return memory.to_dict()

    @app.delete("/api/v1/memories/{memory_id}")
    async def delete_memory(memory_id: str):
        """Delete a memory."""
        success = engine.delete(memory_id)
        if not success:
            raise HTTPException(status_code=404, detail="Memory not found")
        
        return {"success": True}

    @app.get("/api/v1/memories")
    async def list_memories(
        q: Optional[str] = None,
        tags: Optional[str] = None,
        agent: Optional[str] = None,
        limit: int = 10,
        offset: int = 0
    ):
        """List or search memories."""
        # Parse tags
        tag_list = tags.split(",") if tags else None
        
        # Search if query provided
        if q or tag_list or agent:
            memories = engine.search(
                query=q or "",
                tags=tag_list,
                agent=agent,
                limit=limit
            )
        else:
            memories = engine.list_memories(limit=limit, offset=offset)
        
        return {
            "memories": [m.to_dict() for m in memories],
            "total": len(memories)
        }
    
    return app
