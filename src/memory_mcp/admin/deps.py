"""Dependencies for admin routes."""

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from memory_mcp.engine.memory import MemoryEngine

from .api_keys import ApiKeyStore
from .auth import AdminAuth
from .logger import SQLiteLogger, get_logger

# Singleton admin auth instance
_admin_auth: AdminAuth = None


def get_admin_auth() -> AdminAuth:
    """Get singleton admin auth instance."""
    global _admin_auth
    if _admin_auth is None:
        _admin_auth = AdminAuth()
    return _admin_auth


def get_memory_engine(request: Request) -> MemoryEngine:
    """Get memory engine from the FastAPI application state."""
    engine = getattr(request.app.state, "memory_engine", None)
    if engine is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Memory engine not configured",
        )
    return engine


def get_api_key_store(request: Request) -> ApiKeyStore:
    """Get API key store from the FastAPI application state."""
    store = getattr(request.app.state, "api_key_store", None)
    if store is None:
        store = ApiKeyStore()
        request.app.state.api_key_store = store
    return store


def get_admin_logger(request: Request) -> SQLiteLogger:
    """Get admin logger from the FastAPI application state."""
    logger = getattr(request.app.state, "admin_logger", None)
    if logger is None:
        logger = get_logger()
        request.app.state.admin_logger = logger
    return logger


security = HTTPBearer()


async def require_admin_session(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    admin_auth: AdminAuth = Depends(get_admin_auth),
) -> str:
    """Require valid admin session."""
    token = credentials.credentials
    
    if not admin_auth.verify_session(token):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired admin session",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return token
