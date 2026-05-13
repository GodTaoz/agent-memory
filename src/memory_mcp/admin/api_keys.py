"""Persistent API key store for admin-managed REST credentials."""

from __future__ import annotations

import hashlib
import json
import os
import secrets
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Optional


@dataclass
class ApiKeyRecord:
    key_preview: str
    name: str
    permissions: str
    description: Optional[str]
    created_at: str
    last_used: Optional[str]
    usage_count: int
    key_hash: str

    def to_dict(self) -> dict:
        return {
            "key_preview": self.key_preview,
            "name": self.name,
            "permissions": self.permissions,
            "description": self.description,
            "created_at": self.created_at,
            "last_used": self.last_used,
            "usage_count": self.usage_count,
            "key_hash": self.key_hash,
        }

    @classmethod
    def from_dict(cls, payload: dict) -> "ApiKeyRecord":
        return cls(
            key_preview=payload["key_preview"],
            name=payload["name"],
            permissions=payload.get("permissions", "read"),
            description=payload.get("description"),
            created_at=payload["created_at"],
            last_used=payload.get("last_used"),
            usage_count=payload.get("usage_count", 0),
            key_hash=payload["key_hash"],
        )


class ApiKeyStore:
    """JSON-backed API key store with usage tracking."""

    def __init__(self, path: Optional[str] = None, bootstrap_keys: Optional[list[str]] = None):
        default_path = Path(__file__).resolve().parents[3] / "data" / "api_keys.json"
        self.path = Path(path or os.environ.get("ADMIN_API_KEYS_PATH", str(default_path)))
        self.path.parent.mkdir(parents=True, exist_ok=True)
        bootstrap_keys = bootstrap_keys or []
        self._bootstrap_hashes = {self._hash_key(key) for key in bootstrap_keys}
        self._records: list[ApiKeyRecord] = []
        self._enforced = bool(bootstrap_keys)
        self._load()

    def _load(self) -> None:
        if not self.path.exists():
            self._records = []
            return
        payload = json.loads(self.path.read_text(encoding="utf-8"))
        self._records = [ApiKeyRecord.from_dict(item) for item in payload.get("api_keys", [])]
        self._enforced = payload.get("enforced", self._enforced)

    def _save(self) -> None:
        payload = {
            "enforced": self._enforced,
            "api_keys": [record.to_dict() for record in self._records],
        }
        self.path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
        os.chmod(self.path, 0o600)

    @staticmethod
    def _hash_key(full_key: str) -> str:
        return hashlib.sha256(full_key.encode("utf-8")).hexdigest()

    @staticmethod
    def _preview(full_key: str) -> str:
        return f"{full_key[:12]}..."

    def list_keys(self) -> list[dict]:
        return [
            {
                "key_preview": record.key_preview,
                "name": record.name,
                "permissions": record.permissions,
                "description": record.description,
                "created_at": record.created_at,
                "last_used": record.last_used,
                "usage_count": record.usage_count,
            }
            for record in sorted(self._records, key=lambda item: item.created_at, reverse=True)
        ]

    def create_key(self, name: str, permissions: str = "read", description: Optional[str] = None) -> dict:
        full_key = f"amk_{secrets.token_urlsafe(24)}"
        created_at = datetime.now().isoformat()
        record = ApiKeyRecord(
            key_preview=self._preview(full_key),
            name=name,
            permissions=permissions,
            description=description,
            created_at=created_at,
            last_used=None,
            usage_count=0,
            key_hash=self._hash_key(full_key),
        )
        self._records.append(record)
        self._enforced = True
        self._save()
        payload = record.to_dict()
        payload.pop("key_hash", None)
        payload["full_key"] = full_key
        return payload

    def delete_key(self, key_preview: str) -> bool:
        before = len(self._records)
        self._records = [record for record in self._records if record.key_preview != key_preview]
        deleted = len(self._records) != before
        if deleted:
            self._save()
        return deleted

    def has_any_keys(self) -> bool:
        return bool(self._records or self._bootstrap_hashes)

    def is_enforced(self) -> bool:
        return self._enforced

    def validate_key(self, full_key: Optional[str]) -> bool:
        if not full_key:
            return False
        key_hash = self._hash_key(full_key)
        if key_hash in self._bootstrap_hashes:
            return True
        return any(record.key_hash == key_hash for record in self._records)

    def record_usage(self, full_key: Optional[str]) -> None:
        if not full_key:
            return
        key_hash = self._hash_key(full_key)
        for record in self._records:
            if record.key_hash == key_hash:
                record.usage_count += 1
                record.last_used = datetime.now().isoformat()
                self._save()
                return

    def get_key_preview(self, full_key: Optional[str]) -> Optional[str]:
        if not full_key:
            return None
        key_hash = self._hash_key(full_key)
        for record in self._records:
            if record.key_hash == key_hash:
                return record.key_preview
        if key_hash in self._bootstrap_hashes:
            return self._preview(full_key)
        return None

    def get_permissions(self, full_key: Optional[str]) -> Optional[str]:
        if not full_key:
            return None
        key_hash = self._hash_key(full_key)
        for record in self._records:
            if record.key_hash == key_hash:
                return record.permissions
        if key_hash in self._bootstrap_hashes:
            return "admin"
        return None

    def count(self) -> int:
        return len(self._records) + len(self._bootstrap_hashes)
