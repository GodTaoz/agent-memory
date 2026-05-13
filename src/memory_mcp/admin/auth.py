"""Admin authentication module."""

import hashlib
import secrets
import os
from typing import Optional
from datetime import datetime, timedelta


def get_config() -> dict:
    """Get admin configuration."""
    return {
        "admin": {
            "password_hash": os.environ.get("ADMIN_PASSWORD_HASH"),
            "password_salt": os.environ.get("ADMIN_PASSWORD_SALT", ""),
        }
    }


class AdminAuth:
    """Admin authentication handler."""
    
    # Default admin password (should be changed after first login)
    DEFAULT_PASSWORD = "admin123"
    
    # Session duration in hours
    SESSION_DURATION_HOURS = 24
    
    def __init__(self):
        self._sessions: dict[str, dict] = {}
        self._password_hash: Optional[str] = None
        self._load_password()
    
    def _load_password(self):
        """Load admin password hash from config."""
        config = get_config()
        admin_config = config.get("admin", {})
        self._password_hash = admin_config.get("password_hash")
    
    def _hash_password(self, password: str, salt: str = None) -> tuple[str, str]:
        """Hash password with salt."""
        if salt is None:
            salt = secrets.token_hex(16)
        hash_obj = hashlib.sha256(f"{salt}{password}".encode())
        password_hash = hash_obj.hexdigest()
        return password_hash, salt
    
    def verify_password(self, password: str) -> bool:
        """Verify admin password."""
        # If no custom password set, use default
        if self._password_hash is None:
            return password == self.DEFAULT_PASSWORD
        
        # Load salt from config
        config = get_config()
        admin_config = config.get("admin", {})
        salt = admin_config.get("password_salt", "")
        
        # Hash and compare
        password_hash, _ = self._hash_password(password, salt)
        return password_hash == self._password_hash
    
    def change_password(self, old_password: str, new_password: str) -> bool:
        """Change admin password."""
        if not self.verify_password(old_password):
            return False
        
        # Hash new password
        salt = secrets.token_hex(16)
        password_hash, _ = self._hash_password(new_password, salt)
        
        # Update config (in memory, should be persisted to config file)
        self._password_hash = password_hash
        return True
    
    def create_session(self, password: str) -> Optional[str]:
        """Create a new admin session."""
        if not self.verify_password(password):
            return None
        
        # Generate session token
        token = secrets.token_urlsafe(32)
        
        # Store session
        self._sessions[token] = {
            "created_at": datetime.now(),
            "expires_at": datetime.now() + timedelta(hours=self.SESSION_DURATION_HOURS),
        }
        
        return token
    
    def verify_session(self, token: str) -> bool:
        """Verify session token."""
        if token not in self._sessions:
            return False
        
        session = self._sessions[token]
        
        # Check if session expired
        if datetime.now() > session["expires_at"]:
            del self._sessions[token]
            return False
        
        return True
    
    def revoke_session(self, token: str) -> bool:
        """Revoke a session."""
        if token in self._sessions:
            del self._sessions[token]
            return True
        return False
    
    def revoke_all_sessions(self) -> int:
        """Revoke all sessions."""
        count = len(self._sessions)
        self._sessions.clear()
        return count
    
    def get_active_sessions(self) -> list[dict]:
        """Get all active sessions."""
        # Clean expired sessions
        now = datetime.now()
        expired = [t for t, s in self._sessions.items() if now > s["expires_at"]]
        for token in expired:
            del self._sessions[token]
        
        return [
            {
                "token_preview": token[:8] + "...",
                "created_at": s["created_at"].isoformat(),
                "expires_at": s["expires_at"].isoformat(),
            }
            for token, s in self._sessions.items()
        ]
