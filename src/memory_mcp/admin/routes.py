"""Admin API routes."""

import json
import csv
import io
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status, Query
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from .deps import get_admin_auth, require_admin_session
from .auth import AdminAuth

router = APIRouter(prefix="/admin/api", tags=["admin"])


# ============ Request/Response Models ============

class LoginRequest(BaseModel):
    password: str


class LoginResponse(BaseModel):
    token: str
    expires_in: int  # seconds


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


class MemoryItem(BaseModel):
    key: str
    content: str
    tags: list[str]
    created_at: str
    updated_at: str
    agent_id: Optional[str]


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


# ============ Auth Routes ============

@router.post("/auth/login", response_model=LoginResponse)
async def login(request: LoginRequest, admin_auth: AdminAuth = Depends(get_admin_auth)):
    """Admin login."""
    token = admin_auth.create_session(request.password)
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid password"
        )
    
    return LoginResponse(
        token=token,
        expires_in=admin_auth.SESSION_DURATION_HOURS * 3600
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
    admin_auth: AdminAuth = Depends(get_admin_auth)
):
    """Change admin password."""
    success = admin_auth.change_password(request.old_password, request.new_password)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid old password"
        )
    
    # Revoke all sessions after password change
    admin_auth.revoke_all_sessions()
    return {"message": "Password changed successfully. Please login again."}


# ============ System Stats ============

@router.get("/stats", response_model=SystemStats)
async def get_system_stats(token: str = Depends(require_admin_session)):
    """Get system statistics."""
    # TODO: Implement actual stats collection from Redis
    return SystemStats(
        redis_connected=True,
        redis_memory_used="128MB",
        redis_keys_count=150,
        total_memories=100,
        total_agents=5,
        total_api_keys=3,
        uptime_seconds=86400,
        requests_today=1250,
        avg_response_time_ms=15.5
    )


# ============ API Key Management ============

@router.get("/api-keys", response_model=list[ApiKeyResponse])
async def list_api_keys(token: str = Depends(require_admin_session)):
    """List all API keys."""
    # TODO: Implement actual API key listing from config/Redis
    return []


@router.post("/api-keys", response_model=ApiKeyResponse)
async def create_api_key(
    request: ApiKeyCreateRequest,
    token: str = Depends(require_admin_session)
):
    """Create a new API key."""
    # TODO: Implement actual API key creation
    raise HTTPException(status_code=501, detail="Not implemented yet")


@router.delete("/api-keys/{key_preview}")
async def delete_api_key(
    key_preview: str,
    token: str = Depends(require_admin_session)
):
    """Delete an API key."""
    # TODO: Implement actual API key deletion
    raise HTTPException(status_code=501, detail="Not implemented yet")


# ============ Memory Management ============

@router.get("/memories", response_model=list[MemoryItem])
async def list_memories(
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    tag: Optional[str] = None,
    search: Optional[str] = None,
    token: str = Depends(require_admin_session)
):
    """List all memories with pagination and filtering."""
    # TODO: Implement actual memory listing from Redis
    return []


@router.get("/memories/{key}", response_model=MemoryItem)
async def get_memory(
    key: str,
    token: str = Depends(require_admin_session)
):
    """Get a specific memory by key."""
    # TODO: Implement actual memory retrieval
    raise HTTPException(status_code=404, detail="Memory not found")


@router.put("/memories/{key}", response_model=MemoryItem)
async def update_memory(
    key: str,
    request: MemoryUpdateRequest,
    token: str = Depends(require_admin_session)
):
    """Update a memory."""
    # TODO: Implement actual memory update
    raise HTTPException(status_code=501, detail="Not implemented yet")


@router.delete("/memories/{key}")
async def delete_memory(
    key: str,
    token: str = Depends(require_admin_session)
):
    """Delete a memory."""
    # TODO: Implement actual memory deletion
    raise HTTPException(status_code=501, detail="Not implemented yet")


# ============ Memory Export ============

@router.get("/memories/export/json")
async def export_memories_json(
    tag: Optional[str] = None,
    token: str = Depends(require_admin_session)
):
    """Export memories as JSON."""
    # TODO: Implement actual memory export
    memories = []
    
    return StreamingResponse(
        io.BytesIO(json.dumps(memories, indent=2, ensure_ascii=False).encode()),
        media_type="application/json",
        headers={"Content-Disposition": "attachment; filename=memories.json"}
    )


@router.get("/memories/export/csv")
async def export_memories_csv(
    tag: Optional[str] = None,
    token: str = Depends(require_admin_session)
):
    """Export memories as CSV."""
    # TODO: Implement actual memory export
    memories = []
    
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
    token: str = Depends(require_admin_session)
):
    """Get operation logs."""
    # TODO: Implement actual log retrieval from SQLite
    return []
