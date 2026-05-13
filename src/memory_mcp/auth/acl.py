"""Access Control List (ACL) for Memory MCP Server.

This module handles permission checking for multi-agent access.
"""

import logging
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class ACL:
    """Access Control List for memory operations."""

    def __init__(self, config: Dict[str, Any]):
        """Initialize ACL.
        
        Args:
            config: ACL configuration with agents and permissions
        """
        self._config = config

    def _match_namespace(self, pattern: str, resource: str, agent_id: str) -> bool:
        """Check if a resource matches a namespace pattern.
        
        Args:
            pattern: Namespace pattern (e.g., "hermes:*", "${agent_id}:*")
            resource: Resource identifier (e.g., "hermes:memory:123")
            agent_id: Agent identifier
            
        Returns:
            True if resource matches pattern
        """
        # Replace variables in pattern
        resolved_pattern = pattern.replace("${agent_id}", agent_id)
        
        # Handle wildcard patterns
        if resolved_pattern.endswith(":*"):
            prefix = resolved_pattern[:-2]
            return resource.startswith(prefix + ":")
        
        # Exact match
        return resolved_pattern == resource

    def check_permission(
        self,
        agent_id: str,
        operation: str,
        resource: str
    ) -> bool:
        """Check if an agent has permission for an operation on a resource.
        
        Args:
            agent_id: Agent identifier
            operation: Operation type (read, write, delete)
            resource: Resource identifier
            
        Returns:
            True if permission granted
        """
        # Get agent config
        agents = self._config.get("agents", {})
        agent_config = agents.get(agent_id)
        
        # Fall back to default if agent not found
        if agent_config is None:
            agent_config = agents.get("default")
        
        if agent_config is None:
            logger.warning(f"No config found for agent: {agent_id}")
            return False
        
        permissions = agent_config.get("permissions", {})
        
        # Check admin flag
        if permissions.get("admin", False):
            return True
        
        # Check if operation is allowed
        allowed_operations = permissions.get("operations", [])
        if operation not in allowed_operations:
            return False
        
        # Check namespace
        namespace = permissions.get("namespace", "")
        if self._match_namespace(namespace, resource, agent_id):
            return True
        
        # Check shared_read permission
        if permissions.get("shared_read", False) and operation == "read":
            if resource.startswith("shared:"):
                return True
        
        return False

    def get_agent_permissions(self, agent_id: str) -> Optional[Dict[str, Any]]:
        """Get permissions for an agent.
        
        Args:
            agent_id: Agent identifier
            
        Returns:
            Permissions dictionary or None
        """
        agents = self._config.get("agents", {})
        agent_config = agents.get(agent_id)
        
        # Fall back to default if agent not found
        if agent_config is None:
            agent_config = agents.get("default")
        
        if agent_config is None:
            return None
        
        return agent_config.get("permissions", {})

    def list_agents(self) -> List[str]:
        """List all configured agents.
        
        Returns:
            List of agent identifiers
        """
        agents = self._config.get("agents", {})
        return list(agents.keys())
