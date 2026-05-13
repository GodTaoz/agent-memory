"""Tests for admin frontend bundle optimization."""

from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
FRONTEND_ROOT = PROJECT_ROOT / "admin-frontend"
BACKEND_ROOT = PROJECT_ROOT / "src" / "memory_mcp"


def test_main_ts_does_not_register_all_element_plus_icons() -> None:
    """Frontend entry should avoid wildcard icon registration to keep bundle size down."""
    content = (FRONTEND_ROOT / "src" / "main.ts").read_text(encoding="utf-8")

    assert "import * as ElementPlusIconsVue" not in content
    assert "Object.entries(ElementPlusIconsVue)" not in content


def test_vite_config_defines_manual_chunks() -> None:
    """Vite config should define manualChunks for stable vendor splitting."""
    content = (FRONTEND_ROOT / "vite.config.ts").read_text(encoding="utf-8")

    assert "manualChunks" in content
    assert "element-plus" in content
    assert "vue-vendor" in content


def test_memories_view_does_not_depend_on_globally_registered_arrow_down_icon() -> None:
    """Memories view should import ArrowDown explicitly after removing global icon registration."""
    content = (FRONTEND_ROOT / "src" / "views" / "MemoriesView.vue").read_text(encoding="utf-8")

    assert "<arrow-down />" not in content
    assert "ArrowDown" in content
