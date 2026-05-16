"""Tests for application bootstrap auth/ACL loading."""

from __future__ import annotations

import pytest

from memory_mcp import main


def test_load_auth_config_includes_permissions_yaml_when_present(tmp_path, monkeypatch) -> None:
    config_dir = tmp_path / "config"
    config_dir.mkdir()
    (config_dir / "permissions.yaml").write_text(
        """
agents:
  codex:
    permissions:
      namespace: "codex:*"
      operations: ["read", "write"]
      shared_read: true
""".strip()
        + "\n",
        encoding="utf-8",
    )

    monkeypatch.setenv("API_KEYS", "alpha, beta")
    monkeypatch.setattr(main, "_project_root", lambda: tmp_path)

    auth_config = main._load_auth_config()

    assert auth_config["api_keys"] == ["alpha", "beta"]
    assert auth_config["acl"] == {
        "agents": {
            "codex": {
                "permissions": {
                    "namespace": "codex:*",
                    "operations": ["read", "write"],
                    "shared_read": True,
                }
            }
        }
    }



def test_load_auth_config_rejects_non_mapping_permissions_yaml(tmp_path, monkeypatch) -> None:
    config_dir = tmp_path / "config"
    config_dir.mkdir()
    (config_dir / "permissions.yaml").write_text("- invalid\n- acl\n", encoding="utf-8")

    monkeypatch.setattr(main, "_project_root", lambda: tmp_path)

    with pytest.raises(ValueError, match="permissions.yaml"):
        main._load_auth_config()
