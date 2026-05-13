"""Dependencies for admin routes."""

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from .auth import AdminAuth

# Singleton admin auth instance
_admin_auth: AdminAuth = None


def get_admin_auth() -> AdminAuth:
    """Get singleton admin auth instance."""
    global _admin_auth
    if _admin_auth is None:
        _admin_auth = AdminAuth()
    return _admin_auth


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
