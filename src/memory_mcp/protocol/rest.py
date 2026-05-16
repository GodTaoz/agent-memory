"""REST API for Memory MCP Server.

This module implements the REST API endpoints for memory operations.
"""

import logging
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse, FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from memory_mcp.engine.memory import MemoryEngine
from memory_mcp.models import Confidence, Memory
from memory_mcp.auth.acl import ACL
from memory_mcp.auth.middleware import AuthMiddleware
from memory_mcp.admin.api_keys import ApiKeyStore
from memory_mcp.admin.logger import get_logger
from memory_mcp.admin.routes import router as admin_router

logger = logging.getLogger(__name__)

SHARED_AGENT = "shared"


# Request/Response models
class MemoryCreate(BaseModel):
    """Request model for creating a memory."""
    content: str = Field(..., description="Memory content")
    tags: List[str] = Field(default_factory=list, description="Tags")
    agent: str = Field(default="", description="Agent name")
    confidence: Confidence = Field(default=Confidence.HIGH, description="Confidence level")


class MemoryUpdate(BaseModel):
    """Request model for updating a memory."""
    content: Optional[str] = Field(None, description="New content")
    tags: Optional[List[str]] = Field(None, description="New tags")
    confidence: Optional[Confidence] = Field(None, description="New confidence level")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Metadata updates")


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


class HealthResponse(BaseModel):
    """Response model for health checks."""
    status: str
    total_memories: int


class StatsResponse(BaseModel):
    """Response model for memory statistics."""
    total_memories: int


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
    
    auth_config = auth_config or {}
    acl = ACL(auth_config["acl"]) if auth_config.get("acl") else None
    app.state.memory_engine = engine
    app.state.api_key_store = ApiKeyStore(bootstrap_keys=auth_config.get("api_keys", []))
    app.state.admin_logger = get_logger()
    app.state.started_at = datetime.now()
    app.state.acl = acl

    # Include admin routes
    app.include_router(admin_router)
    
    # Initialize auth middleware
    auth_middleware = AuthMiddleware({**auth_config, "api_key_store": app.state.api_key_store})
    
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

        if not path.startswith("/api/v1"):
            return await call_next(request)
        
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

        key_permissions = app.state.api_key_store.get_permissions(api_key)
        key_agent_id = app.state.api_key_store.get_agent_id(api_key)
        request.state.api_key_permissions = key_permissions
        request.state.api_key_agent_id = key_agent_id
        if (
            app.state.api_key_store.is_enforced()
            and request.method in {"POST", "PUT", "PATCH", "DELETE"}
            and key_permissions not in {"read_write", "admin"}
        ):
            return JSONResponse(
                status_code=403,
                content={"error": "API key does not have write permissions"}
            )

        started = time.perf_counter()
        response = await call_next(request)
        response_time_ms = round((time.perf_counter() - started) * 1000, 2)
        auth_middleware.record_usage(api_key)
        app.state.admin_logger.log_api_access(
            method=request.method,
            path=path,
            status_code=response.status_code,
            response_time_ms=response_time_ms,
            api_key_preview=app.state.api_key_store.get_key_preview(api_key),
            ip_address=request.client.host if request.client else None,
        )
        return response

    def _request_permissions(request: Request) -> Optional[str]:
        return getattr(request.state, "api_key_permissions", None)

    def _request_agent_id(request: Request) -> Optional[str]:
        return getattr(request.state, "api_key_agent_id", None)

    def _request_acl(request: Request) -> Optional[ACL]:
        return getattr(request.app.state, "acl", None)

    def _is_admin_request(request: Request) -> bool:
        return _request_permissions(request) == "admin"

    def _memory_resource(memory: Memory) -> str:
        return f"{memory.agent}:memory:{memory.id}"

    def _namespace_resource(agent_name: str) -> str:
        return f"{agent_name}:memory:__scope__"

    def _acl_allows(request: Request, operation: str, resource: str) -> bool:
        acl = _request_acl(request)
        agent_id = _request_agent_id(request)
        if acl is None or not agent_id or _is_admin_request(request):
            return True
        return acl.check_permission(agent_id, operation, resource)

    def _can_access_memory(request: Request, memory: Memory) -> bool:
        if _is_admin_request(request):
            return True
        agent_id = _request_agent_id(request)
        if not agent_id:
            return True
        if _request_acl(request) is not None:
            return _acl_allows(request, "read", _memory_resource(memory))
        return memory.agent in {agent_id, SHARED_AGENT}

    def _enforce_memory_visibility(request: Request, memory: Memory) -> None:
        if not _can_access_memory(request, memory):
            raise HTTPException(status_code=403, detail="Memory belongs to another agent")

    def _enforce_memory_write_access(request: Request, memory: Memory, operation: str = "write") -> None:
        if _is_admin_request(request):
            return
        agent_id = _request_agent_id(request)
        if not agent_id:
            return
        if _request_acl(request) is not None:
            if not _acl_allows(request, operation, _memory_resource(memory)):
                raise HTTPException(status_code=403, detail="API key is not allowed to modify this memory")
            return
        if memory.agent != agent_id:
            raise HTTPException(status_code=403, detail="API key cannot modify this memory")

    def _resolve_create_agent(request: Request, requested_agent: str) -> str:
        if _is_admin_request(request):
            return requested_agent
        agent_id = _request_agent_id(request)
        if not agent_id:
            return requested_agent
        if requested_agent == SHARED_AGENT:
            raise HTTPException(status_code=403, detail="Only admin API keys can write shared memories")
        if requested_agent and requested_agent != agent_id:
            raise HTTPException(status_code=403, detail="API key cannot write memories for another agent")
        resolved_agent = agent_id
        if _request_acl(request) is not None and not _acl_allows(
            request,
            "write",
            _namespace_resource(resolved_agent),
        ):
            raise HTTPException(status_code=403, detail="API key is not allowed to write this namespace")
        return resolved_agent
    
    @app.get("/api/v1/health", response_model=HealthResponse)
    async def health():
        """Health check endpoint."""
        count = engine.count()
        return {"status": "healthy", "total_memories": count}

    @app.get("/api/v1/stats", response_model=StatsResponse)
    async def stats():
        """Statistics endpoint."""
        count = engine.count()
        return {"total_memories": count}

    @app.post("/api/v1/memories", response_model=MemoryResponse, status_code=201)
    async def create_memory(request: MemoryCreate, http_request: Request):
        """Create a new memory."""
        memory = Memory(
            id=engine.generate_id(),
            content=request.content,
            tags=request.tags,
            agent=_resolve_create_agent(http_request, request.agent),
            confidence=request.confidence
        )
        
        success = engine.save(memory)
        if not success:
            raise HTTPException(status_code=500, detail="Failed to save memory")
        
        return memory.to_dict()

    @app.get("/api/v1/memories/{memory_id}", response_model=MemoryResponse)
    async def get_memory(memory_id: str, request: Request):
        """Get a memory by ID."""
        memory = engine.get(memory_id)
        if memory is None:
            raise HTTPException(status_code=404, detail="Memory not found")
        _enforce_memory_visibility(request, memory)

        return memory.to_dict()

    @app.put("/api/v1/memories/{memory_id}", response_model=MemoryResponse)
    async def update_memory(memory_id: str, request: MemoryUpdate, http_request: Request):
        """Update an existing memory."""
        existing_memory = engine.get(memory_id)
        if existing_memory is None:
            raise HTTPException(status_code=404, detail="Memory not found")
        _enforce_memory_write_access(http_request, existing_memory)

        updates = {}
        if request.content is not None:
            updates["content"] = request.content
        if request.tags is not None:
            updates["tags"] = request.tags
        if request.confidence is not None:
            updates["confidence"] = request.confidence.value
        if request.metadata is not None:
            updates["metadata"] = request.metadata

        memory = engine.update(memory_id, updates)
        if memory is None:
            raise HTTPException(status_code=404, detail="Memory not found")

        return memory.to_dict()

    @app.delete(
        "/api/v1/memories/{memory_id}",
        response_model=SuccessResponse,
        response_model_exclude_none=True,
    )
    async def delete_memory(memory_id: str, request: Request):
        """Delete a memory."""
        existing_memory = engine.get(memory_id)
        if existing_memory is None:
            raise HTTPException(status_code=404, detail="Memory not found")
        _enforce_memory_write_access(request, existing_memory, operation="delete")

        success = engine.delete(memory_id)
        if not success:
            raise HTTPException(status_code=404, detail="Memory not found")

        return {"success": True}

    @app.get("/api/v1/memories", response_model=MemoryListResponse)
    async def list_memories(
        request: Request,
        q: Optional[str] = None,
        tags: Optional[str] = None,
        agent: Optional[str] = None,
        limit: int = 10,
        offset: int = 0
    ):
        """List or search memories."""
        tag_list = tags.split(",") if tags else None
        visible_agent = _request_agent_id(request)

        if not _is_admin_request(request) and visible_agent and agent:
            if _request_acl(request) is not None:
                if not _acl_allows(request, "read", _namespace_resource(agent)):
                    raise HTTPException(status_code=403, detail="API key cannot access another agent namespace")
            elif agent not in {visible_agent, SHARED_AGENT}:
                raise HTTPException(status_code=403, detail="API key cannot access another agent namespace")

        total_count = engine.count()
        if q or tag_list or agent:
            memories = engine.search(
                query=q or "",
                tags=tag_list,
                agent=agent,
                limit=total_count,
            )
        else:
            memories = engine.list_memories(limit=total_count, offset=0)

        if not _is_admin_request(request) and visible_agent:
            if _request_acl(request) is not None:
                memories = [
                    memory
                    for memory in memories
                    if _acl_allows(request, "read", _memory_resource(memory))
                ]
            else:
                allowed_agents = {visible_agent, SHARED_AGENT}
                if agent == visible_agent:
                    allowed_agents = {visible_agent}
                elif agent == SHARED_AGENT:
                    allowed_agents = {SHARED_AGENT}
                memories = [memory for memory in memories if memory.agent in allowed_agents]

        paginated_memories = memories[offset : offset + limit]

        return {
            "memories": [m.to_dict() for m in paginated_memories],
            "total": len(paginated_memories)
        }
    
    # Serve admin frontend static files
    static_dir = Path(__file__).resolve().parent.parent / "admin" / "static"
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
