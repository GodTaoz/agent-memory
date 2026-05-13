"""Tests for ACL (Access Control List)."""

import pytest
from unittest.mock import MagicMock
from memory_mcp.auth.acl import ACL


class TestACL:
    """Test ACL class."""

    def test_init(self):
        """Test initializing ACL."""
        config = {
            "agents": {
                "hermes": {
                    "permissions": {
                        "namespace": "hermes:*",
                        "operations": ["read", "write", "delete"],
                        "admin": True
                    }
                }
            }
        }
        acl = ACL(config)
        
        assert acl._config == config

    def test_check_permission_read(self):
        """Test checking read permission."""
        config = {
            "agents": {
                "hermes": {
                    "permissions": {
                        "namespace": "hermes:*",
                        "operations": ["read", "write", "delete"]
                    }
                }
            }
        }
        acl = ACL(config)
        
        # Should allow reading hermes memories
        assert acl.check_permission("hermes", "read", "hermes:memory:123") is True

    def test_check_permission_write(self):
        """Test checking write permission."""
        config = {
            "agents": {
                "hermes": {
                    "permissions": {
                        "namespace": "hermes:*",
                        "operations": ["read", "write", "delete"]
                    }
                }
            }
        }
        acl = ACL(config)
        
        # Should allow writing hermes memories
        assert acl.check_permission("hermes", "write", "hermes:memory:123") is True

    def test_check_permission_denied(self):
        """Test permission denied."""
        config = {
            "agents": {
                "hermes": {
                    "permissions": {
                        "namespace": "hermes:*",
                        "operations": ["read", "write"]
                    }
                }
            }
        }
        acl = ACL(config)
        
        # Should deny delete operation
        assert acl.check_permission("hermes", "delete", "hermes:memory:123") is False

    def test_check_permission_wrong_namespace(self):
        """Test permission denied for wrong namespace."""
        config = {
            "agents": {
                "hermes": {
                    "permissions": {
                        "namespace": "hermes:*",
                        "operations": ["read", "write"]
                    }
                }
            }
        }
        acl = ACL(config)
        
        # Should deny reading codex memories
        assert acl.check_permission("hermes", "read", "codex:memory:123") is False

    def test_check_permission_default_agent(self):
        """Test permission for unknown agent using defaults."""
        config = {
            "agents": {
                "default": {
                    "permissions": {
                        "namespace": "${agent_id}:*",
                        "operations": ["read", "write"]
                    }
                }
            }
        }
        acl = ACL(config)
        
        # Unknown agent should use default permissions
        assert acl.check_permission("codex", "read", "codex:memory:123") is True
        assert acl.check_permission("codex", "write", "codex:memory:123") is True
        assert acl.check_permission("codex", "delete", "codex:memory:123") is False

    def test_check_permission_admin(self):
        """Test admin permission."""
        config = {
            "agents": {
                "hermes": {
                    "permissions": {
                        "namespace": "hermes:*",
                        "operations": ["read", "write"],
                        "admin": True
                    }
                }
            }
        }
        acl = ACL(config)
        
        # Admin should have all permissions
        assert acl.check_permission("hermes", "read", "hermes:memory:123") is True
        assert acl.check_permission("hermes", "write", "hermes:memory:123") is True
        assert acl.check_permission("hermes", "delete", "hermes:memory:123") is True

    def test_check_permission_shared_read(self):
        """Test shared read permission."""
        config = {
            "agents": {
                "codex": {
                    "permissions": {
                        "namespace": "codex:*",
                        "operations": ["read", "write"],
                        "shared_read": True
                    }
                }
            }
        }
        acl = ACL(config)
        
        # Should allow reading codex memories
        assert acl.check_permission("codex", "read", "codex:memory:123") is True
        
        # Should allow reading shared memories
        assert acl.check_permission("codex", "read", "shared:memory:123") is True
        
        # Should deny writing shared memories
        assert acl.check_permission("codex", "write", "shared:memory:123") is False

    def test_get_agent_permissions(self):
        """Test getting agent permissions."""
        config = {
            "agents": {
                "hermes": {
                    "name": "Hermes Agent",
                    "permissions": {
                        "namespace": "hermes:*",
                        "operations": ["read", "write", "delete"]
                    }
                }
            }
        }
        acl = ACL(config)
        
        perms = acl.get_agent_permissions("hermes")
        
        assert perms is not None
        assert perms["namespace"] == "hermes:*"
        assert "read" in perms["operations"]
        assert "write" in perms["operations"]

    def test_get_agent_permissions_unknown(self):
        """Test getting permissions for unknown agent."""
        config = {
            "agents": {
                "default": {
                    "permissions": {
                        "namespace": "${agent_id}:*",
                        "operations": ["read", "write"]
                    }
                }
            }
        }
        acl = ACL(config)
        
        perms = acl.get_agent_permissions("unknown")
        
        # Should return default permissions
        assert perms is not None
        assert perms["operations"] == ["read", "write"]

    def test_list_agents(self):
        """Test listing configured agents."""
        config = {
            "agents": {
                "hermes": {"permissions": {"namespace": "hermes:*"}},
                "codex": {"permissions": {"namespace": "codex:*"}},
                "default": {"permissions": {"namespace": "${agent_id}:*"}}
            }
        }
        acl = ACL(config)
        
        agents = acl.list_agents()
        
        assert "hermes" in agents
        assert "codex" in agents
        assert "default" in agents
