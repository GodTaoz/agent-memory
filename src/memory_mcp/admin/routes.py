"""Admin API routes."""

import json
import csv
import io
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Request, status, Query
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from .deps import get_admin_auth, get_admin_logger, get_api_key_store, get_memory_engine, require_admin_session
from .api_keys import ApiKeyStore
from .auth import AdminAuth
from .logger import SQLiteLogger
from memory_mcp.engine.memory import MemoryEngine

router = APIRouter(prefix="/admin/api", tags=["admin"])


# ============ Request/Response Models ============

class LoginRequest(BaseModel):
    password: str


class LoginResponse(BaseModel):
    token: str
    expires_in: int  # seconds
    requires_password_change: bool = False


class ChangePasswordRequest(BaseModel):
    old_password: str
    new_password: str


class ApiKeyCreateRequest(BaseModel):
    name: str
    permissions: str = "read"  # read, read_write, admin
    description: Optional[str] = None


class ApiKeyResponse(BaseModel):
    key_preview: str
    name: str
    permissions: str
    description: Optional[str]
    created_at: str
    last_used: Optional[str]
    usage_count: int
    full_key: Optional[str] = None


class MemoryItem(BaseModel):
    key: str
    content: str
    tags: list[str]
    created_at: str
    updated_at: str
    agent_id: Optional[str]


class MemoryListResponse(BaseModel):
    memories: list[MemoryItem]
    total: int


class MemoryUpdateRequest(BaseModel):
    content: Optional[str] = None
    tags: Optional[list[str]] = None


class AgentInfo(BaseModel):
    agent_id: str
    name: Optional[str]
    permissions: str
    last_active: Optional[str]
    memory_count: int
    api_key_preview: str


class LogEntry(BaseModel):
    timestamp: str
    level: str
    message: str
    details: Optional[dict]


class SystemStats(BaseModel):
    redis_connected: bool
    redis_memory_used: str
    redis_keys_count: int
    total_memories: int
    total_agents: int
    total_api_keys: int
    uptime_seconds: int
    requests_today: int
    avg_response_time_ms: float


def _memory_to_item(memory) -> MemoryItem:
    return MemoryItem(
        key=memory.id,
        content=memory.content,
        tags=memory.tags,
        created_at=memory.created_at.isoformat(),
        updated_at=memory.updated_at.isoformat(),
        agent_id=memory.agent or None,
    )


def _collect_memories(
    engine: MemoryEngine,
    *,
    tag: Optional[str] = None,
    search: Optional[str] = None,
) -> list:
    if tag or search:
        return engine.search(
            query=search or None,
            tags=[tag] if tag else None,
            limit=engine.count(),
        )
    return engine.list_memories(limit=engine.count(), offset=0)


def _get_redis_stats(engine: MemoryEngine) -> tuple[bool, str, int]:
    backend = getattr(engine, "_backend", None)
    client = getattr(backend, "_client", None)
    if client is None:
        return False, "-", 0

    try:
        client.ping()
        info = client.info()
        if not isinstance(info, dict):
            return False, "-", 0

        key_prefix = getattr(backend, "key_prefix", "memory")
        keys = client.keys(f"{key_prefix}:*")
        redis_keys_count = len(keys) if isinstance(keys, (list, tuple, set)) else 0
        redis_memory_used = info.get("used_memory_human", "-")
        if not isinstance(redis_memory_used, str):
            redis_memory_used = "-"
        return True, redis_memory_used, redis_keys_count
    except Exception:
        return False, "-", 0


def _count_agents(memories: list) -> int:
    return len({memory.agent for memory in memories if getattr(memory, "agent", None)})


# ============ Auth Routes ============

@router.post("/auth/login", response_model=LoginResponse)
async def login(
    credentials: LoginRequest,
    request: Request,
    admin_auth: AdminAuth = Depends(get_admin_auth),
    admin_logger: SQLiteLogger = Depends(get_admin_logger),
):
    """Admin login."""
    token = admin_auth.create_session(credentials.password)
    client_ip = request.client.host if request.client else None
    if not token:
        if admin_auth.is_locked_out():
            admin_logger.log_login(False, client_ip, "locked out")
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Too many failed login attempts. Please try again later.",
            )
        admin_logger.log_login(False, client_ip, "invalid password")
        admin_logger.log_operation("warning", "auth", "Admin login failed", ip_address=client_ip)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid password"
        )

    admin_logger.log_login(True, client_ip)
    admin_logger.log_operation("info", "auth", "Admin login succeeded", ip_address=client_ip)
    return LoginResponse(
        token=token,
        expires_in=admin_auth.SESSION_DURATION_HOURS * 3600,
        requires_password_change=admin_auth.requires_password_change(),
    )


@router.post("/auth/logout")
async def logout(
    token: str = Depends(require_admin_session),
    admin_auth: AdminAuth = Depends(get_admin_auth)
):
    """Admin logout."""
    admin_auth.revoke_session(token)
    return {"message": "Logged out successfully"}


@router.post("/auth/change-password")
async def change_password(
    request: ChangePasswordRequest,
    http_request: Request,
    admin_auth: AdminAuth = Depends(get_admin_auth),
    admin_logger: SQLiteLogger = Depends(get_admin_logger),
):
    """Change admin password."""
    success = admin_auth.change_password(request.old_password, request.new_password)
    client_ip = http_request.client.host if http_request.client else None
    if not success:
        admin_logger.log_operation("warning", "auth", "Admin password change failed", ip_address=client_ip)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid old password"
        )

    # Revoke all sessions after password change
    admin_auth.revoke_all_sessions()
    admin_logger.log_operation("info", "auth", "Admin password changed", ip_address=client_ip)
    return {"message": "Password changed successfully. Please login again."}


# ============ System Stats ============

@router.get("/stats", response_model=SystemStats)
async def get_system_stats(
    request: Request,
    token: str = Depends(require_admin_session),
    engine: MemoryEngine = Depends(get_memory_engine),
    api_key_store: ApiKeyStore = Depends(get_api_key_store),
    admin_logger: SQLiteLogger = Depends(get_admin_logger),
):
    """Get system statistics."""
    redis_connected, redis_memory_used, redis_keys_count = _get_redis_stats(engine)
    memories = _collect_memories(engine)
    log_stats = admin_logger.get_stats()
    started_at = getattr(request.app.state, "started_at", None)
    uptime_seconds = 0
    if started_at is not None:
        uptime_seconds = max(0, int((datetime.now() - started_at).total_seconds()))

    return SystemStats(
        redis_connected=redis_connected,
        redis_memory_used=redis_memory_used,
        redis_keys_count=redis_keys_count,
        total_memories=engine.count(),
        total_agents=_count_agents(memories),
        total_api_keys=api_key_store.count(),
        uptime_seconds=uptime_seconds,
        requests_today=log_stats["today_api_calls"],
        avg_response_time_ms=log_stats["avg_response_time_ms"],
    )


# ============ API Key Management ============

@router.get("/api-keys", response_model=list[ApiKeyResponse])
async def list_api_keys(
    token: str = Depends(require_admin_session),
    api_key_store: ApiKeyStore = Depends(get_api_key_store),
):
    """List all API keys."""
    return [ApiKeyResponse(**payload) for payload in api_key_store.list_keys()]


@router.post("/api-keys", response_model=ApiKeyResponse, status_code=201)
async def create_api_key(
    request: ApiKeyCreateRequest,
    http_request: Request,
    token: str = Depends(require_admin_session),
    api_key_store: ApiKeyStore = Depends(get_api_key_store),
    admin_logger: SQLiteLogger = Depends(get_admin_logger),
):
    """Create a new API key."""
    payload = api_key_store.create_key(
        name=request.name,
        permissions=request.permissions,
        description=request.description,
    )
    client_ip = http_request.client.host if http_request.client else None
    admin_logger.log_operation("info", "api_key", f"Created API key {payload['key_preview']}", details={"name": request.name, "permissions": request.permissions}, ip_address=client_ip)
    return ApiKeyResponse(**payload)


@router.delete("/api-keys/{key_preview}")
async def delete_api_key(
    key_preview: str,
    request: Request,
    token: str = Depends(require_admin_session),
    api_key_store: ApiKeyStore = Depends(get_api_key_store),
    admin_logger: SQLiteLogger = Depends(get_admin_logger),
):
    """Delete an API key."""
    if not api_key_store.delete_key(key_preview):
        raise HTTPException(status_code=404, detail="API key not found")
    client_ip = request.client.host if request.client else None
    admin_logger.log_operation("info", "api_key", f"Deleted API key {key_preview}", ip_address=client_ip)
    return {"success": True}


# ============ Memory Management ============

@router.get("/memories", response_model=MemoryListResponse)
async def list_memories(
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    tag: Optional[str] = None,
    search: Optional[str] = None,
    token: str = Depends(require_admin_session),
    engine: MemoryEngine = Depends(get_memory_engine),
):
    """List all memories with pagination and filtering."""
    all_memories = _collect_memories(engine, tag=tag, search=search)
    offset = (page - 1) * page_size
    paginated = all_memories[offset : offset + page_size]
    return MemoryListResponse(
        memories=[_memory_to_item(memory) for memory in paginated],
        total=len(all_memories),
    )


@router.get("/memories/{key}", response_model=MemoryItem)
async def get_memory(
    key: str,
    token: str = Depends(require_admin_session),
    engine: MemoryEngine = Depends(get_memory_engine),
):
    """Get a specific memory by key."""
    memory = engine.get(key)
    if memory is None:
        raise HTTPException(status_code=404, detail="Memory not found")
    return _memory_to_item(memory)


@router.put("/memories/{key}", response_model=MemoryItem)
async def update_memory(
    key: str,
    request: MemoryUpdateRequest,
    http_request: Request,
    token: str = Depends(require_admin_session),
    engine: MemoryEngine = Depends(get_memory_engine),
    admin_logger: SQLiteLogger = Depends(get_admin_logger),
):
    """Update a memory."""
    updates = {}
    if request.content is not None:
        updates["content"] = request.content
    if request.tags is not None:
        updates["tags"] = request.tags

    memory = engine.update(key, updates)
    if memory is None:
        raise HTTPException(status_code=404, detail="Memory not found")
    client_ip = http_request.client.host if http_request.client else None
    admin_logger.log_operation("info", "memory", f"Updated memory {key}", ip_address=client_ip)
    return _memory_to_item(memory)


@router.delete("/memories/{key}")
async def delete_memory(
    key: str,
    request: Request,
    token: str = Depends(require_admin_session),
    engine: MemoryEngine = Depends(get_memory_engine),
    admin_logger: SQLiteLogger = Depends(get_admin_logger),
):
    """Delete a memory."""
    if not engine.delete(key):
        raise HTTPException(status_code=404, detail="Memory not found")
    client_ip = request.client.host if request.client else None
    admin_logger.log_operation("info", "memory", f"Deleted memory {key}", ip_address=client_ip)
    return {"success": True}


# ============ Memory Export ============

@router.get("/memories/export/json")
async def export_memories_json(
    tag: Optional[str] = None,
    token: str = Depends(require_admin_session),
    engine: MemoryEngine = Depends(get_memory_engine),
):
    """Export memories as JSON."""
    memories = [_memory_to_item(memory).model_dump() for memory in _collect_memories(engine, tag=tag)]
    
    return StreamingResponse(
        io.BytesIO(json.dumps(memories, indent=2, ensure_ascii=False).encode()),
        media_type="application/json",
        headers={"Content-Disposition": "attachment; filename=memories.json"}
    )


@router.get("/memories/export/csv")
async def export_memories_csv(
    tag: Optional[str] = None,
    token: str = Depends(require_admin_session),
    engine: MemoryEngine = Depends(get_memory_engine),
):
    """Export memories as CSV."""
    memories = [_memory_to_item(memory).model_dump() for memory in _collect_memories(engine, tag=tag)]
    
    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=["key", "content", "tags", "created_at", "updated_at", "agent_id"])
    writer.writeheader()
    for memory in memories:
        writer.writerow(memory)
    
    return StreamingResponse(
        io.BytesIO(output.getvalue().encode()),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=memories.csv"}
    )


# ============ Agent Management ============

@router.get("/agents", response_model=list[AgentInfo])
async def list_agents(token: str = Depends(require_admin_session)):
    """List all registered agents."""
    # TODO: Implement actual agent listing
    return []


# ============ Operation Logs ============

@router.get("/logs", response_model=list[LogEntry])
async def get_logs(
    level: Optional[str] = None,
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    token: str = Depends(require_admin_session),
    admin_logger: SQLiteLogger = Depends(get_admin_logger),
):
    """Get operation logs."""
    return [LogEntry(**entry) for entry in admin_logger.get_operation_logs(level=level, limit=limit, offset=offset)]
