"""Admin authentication module."""

from __future__ import annotations

import hashlib
import json
import os
import secrets
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional


def get_config() -> dict:
    """Get admin configuration from environment variables."""
    project_root = Path(__file__).resolve().parents[3]
    default_config_path = project_root / "data" / "admin_auth.json"
    configured_path = os.environ.get("ADMIN_AUTH_CONFIG_PATH")

    return {
        "admin": {
            "config_path": configured_path or str(default_config_path),
            "password_hash": os.environ.get("ADMIN_PASSWORD_HASH"),
            "password_salt": os.environ.get("ADMIN_PASSWORD_SALT", ""),
        }
    }


class AdminAuth:
    """Admin authentication handler."""

    DEFAULT_PASSWORD = "admin123"
    SESSION_DURATION_HOURS = 24
    MAX_FAILED_ATTEMPTS = 5
    LOCKOUT_MINUTES = 15

    def __init__(self):
        self._sessions: dict[str, dict] = {}
        self._password_hash: Optional[str] = None
        self._password_salt: str = ""
        self._config_path = Path(get_config()["admin"]["config_path"])
        self._failed_attempts = 0
        self._lockout_until: Optional[datetime] = None
        self._load_password()

    def _load_password(self) -> None:
        """Load admin password hash from config file or environment."""
        config = get_config()["admin"]

        if self._config_path.exists():
            try:
                data = json.loads(self._config_path.read_text(encoding="utf-8"))
                self._password_hash = data.get("password_hash")
                self._password_salt = data.get("password_salt", "")
                return
            except (json.JSONDecodeError, OSError, TypeError):
                # Fall back to env/default behavior when persisted config is invalid.
                pass

        self._password_hash = config.get("password_hash")
        self._password_salt = config.get("password_salt", "")

    def _save_password(self) -> None:
        """Persist admin password hash to local config file."""
        self._config_path.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "password_hash": self._password_hash,
            "password_salt": self._password_salt,
            "updated_at": datetime.now().isoformat(),
        }
        self._config_path.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        os.chmod(self._config_path, 0o600)

    def _hash_password(self, password: str, salt: Optional[str] = None) -> tuple[str, str]:
        """Hash password with salt."""
        if salt is None:
            salt = secrets.token_hex(16)
        hash_obj = hashlib.sha256(f"{salt}{password}".encode())
        password_hash = hash_obj.hexdigest()
        return password_hash, salt

    def verify_password(self, password: str) -> bool:
        """Verify admin password."""
        if self._password_hash is None:
            return password == self.DEFAULT_PASSWORD

        password_hash, _ = self._hash_password(password, self._password_salt)
        return password_hash == self._password_hash

    def is_default_password(self) -> bool:
        """Return whether the admin account still uses the built-in default password."""
        return self._password_hash is None

    def requires_password_change(self) -> bool:
        """Whether the admin should be forced/warned to change the default password."""
        return self.is_default_password()

    def is_locked_out(self) -> bool:
        """Return whether login is temporarily locked due to repeated failures."""
        if self._lockout_until is None:
            return False
        if datetime.now() >= self._lockout_until:
            self._lockout_until = None
            self._failed_attempts = 0
            return False
        return True

    def _record_failed_attempt(self) -> None:
        self._failed_attempts += 1
        if self._failed_attempts >= self.MAX_FAILED_ATTEMPTS:
            self._lockout_until = datetime.now() + timedelta(minutes=self.LOCKOUT_MINUTES)

    def _reset_failed_attempts(self) -> None:
        self._failed_attempts = 0
        self._lockout_until = None

    def change_password(self, old_password: str, new_password: str) -> bool:
        """Change admin password and persist it."""
        if not self.verify_password(old_password):
            return False

        password_hash, salt = self._hash_password(new_password)
        self._password_hash = password_hash
        self._password_salt = salt
        self._reset_failed_attempts()
        self._save_password()
        return True

    def create_session(self, password: str) -> Optional[str]:
        """Create a new admin session."""
        if self.is_locked_out():
            return None

        if not self.verify_password(password):
            self._record_failed_attempt()
            return None

        self._reset_failed_attempts()
        token = secrets.token_urlsafe(32)
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
