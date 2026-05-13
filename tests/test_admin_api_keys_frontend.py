"""Tests for admin API key frontend behavior expectations."""

from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
API_KEYS_VIEW = PROJECT_ROOT / "admin-frontend" / "src" / "views" / "ApiKeysView.vue"


def test_api_keys_view_stores_created_full_key_from_response() -> None:
    content = API_KEYS_VIEW.read_text(encoding="utf-8")
    assert "response.data.full_key" in content


def test_api_keys_view_can_copy_created_full_key() -> None:
    content = API_KEYS_VIEW.read_text(encoding="utf-8")
    assert "createdKey?.full_key && copyKey(createdKey.full_key)" in content
