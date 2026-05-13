"""REST API for Memory MCP Server.

This module implements the REST API endpoints for memory operations.
"""

import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse, FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from memory_mcp.engine.memory import MemoryEngine
from memory_mcp.models import Memory
from memory_mcp.auth.middleware import AuthMiddleware
from memory_mcp.admin.routes import router as admin_router

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


def create_app(engine: MemoryEngine, auth_config: Optional[Dict[str, Any]] = None) -> FastAPI:
    """Create FastAPI application.
    
    Args:
        engine: Memory engine instance
        auth_config: Authentication configuration (optional)
        
    Returns:
        FastAPI application
    """
    app = FastAPI(
        title="Memory MCP Server",
        description="Universal Memory Service for AI Agents",
        version="0.1.0"
    )
    
    # Include admin routes
    app.include_router(admin_router)
    
    # Initialize auth middleware
    auth_middleware = AuthMiddleware(auth_config or {})
    
    # Paths that don't require API key authentication
    PUBLIC_PATHS = [
        "/api/v1/health",
        "/admin/",
        "/admin/api/auth/login",
    ]
    
    @app.middleware("http")
    async def auth_middleware_handler(request: Request, call_next):
        """Authentication middleware."""
        path = request.url.path
        
        # Skip auth for public paths and admin panel
        if any(path.startswith(p) for p in PUBLIC_PATHS):
            return await call_next(request)
        
        # Skip auth for static files (admin frontend)
        if path.startswith("/assets/") or path.endswith((".js", ".css", ".ico", ".svg", ".png")):
            return await call_next(request)
        
        # Extract API key
        api_key = auth_middleware.extract_api_key(
            dict(request.headers),
            dict(request.query_params)
        )
        
        # Validate API key
        if not auth_middleware.validate_api_key(api_key):
            return JSONResponse(
                status_code=401,
                content={"error": "Invalid or missing API key"}
            )
        
        return await call_next(request)
    
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
    
    # Serve admin frontend static files
    static_dir = Path(__file__).parent.parent.parent / "admin" / "static"
    if static_dir.exists():
        app.mount("/assets", StaticFiles(directory=str(static_dir / "assets")), name="assets")
        
        @app.get("/", response_class=HTMLResponse)
        async def root():
            """Redirect to admin panel."""
            index_path = static_dir / "index.html"
            if index_path.exists():
                return FileResponse(str(index_path))
            return HTMLResponse("<h1>Admin panel not built yet</h1><p>Run: cd admin-frontend && npm run build</p>")
        
        @app.get("/{path:path}", response_class=HTMLResponse)
        async def catch_all(path: str):
            """Catch-all route for Vue Router."""
            # Check if file exists in static directory
            file_path = static_dir / path
            if file_path.exists() and file_path.is_file():
                return FileResponse(str(file_path))
            
            # Return index.html for Vue Router
            index_path = static_dir / "index.html"
            if index_path.exists():
                return FileResponse(str(index_path))
            
            return HTMLResponse("<h1>Admin panel not built yet</h1>", status_code=404)
    else:
        @app.get("/")
        async def root():
            return {"message": "Agent Memory API", "docs": "/docs", "admin": "Build admin-frontend first"}
    
    return app
