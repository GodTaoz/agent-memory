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
        self._validate_config(config)
        self._config = config

    def _validate_config(self, config: Dict[str, Any]) -> None:
        """Validate ACL config structure eagerly so malformed ACL fails closed."""
        if not isinstance(config, dict):
            raise ValueError("ACL config must be a mapping")

        shared_namespaces = config.get("shared_namespaces")
        if shared_namespaces is not None:
            if not isinstance(shared_namespaces, list) or not all(
                isinstance(namespace, str) for namespace in shared_namespaces
            ):
                raise ValueError(
                    "ACL config field 'shared_namespaces' must be a list of strings"
                )

        agents = config.get("agents", {})
        if not isinstance(agents, dict):
            raise ValueError("ACL config field 'agents' must be a mapping")

        for agent_name, agent_config in agents.items():
            if not isinstance(agent_config, dict):
                raise ValueError(f"ACL config for agent '{agent_name}' must be a mapping")

            permissions = agent_config.get("permissions", {})
            if not isinstance(permissions, dict):
                raise ValueError(
                    f"ACL permissions for agent '{agent_name}' must be a mapping"
                )

            namespace = permissions.get("namespace")
            if namespace is not None and not isinstance(namespace, str):
                raise ValueError(
                    f"ACL namespace for agent '{agent_name}' must be a string"
                )

            operations = permissions.get("operations")
            if operations is not None:
                if not isinstance(operations, list) or not all(
                    isinstance(operation, str) for operation in operations
                ):
                    raise ValueError(
                        f"ACL operations for agent '{agent_name}' must be a list of strings"
                    )

            for flag_name in ("admin", "shared_read"):
                flag_value = permissions.get(flag_name)
                if flag_value is not None and not isinstance(flag_value, bool):
                    raise ValueError(
                        f"ACL flag '{flag_name}' for agent '{agent_name}' must be a boolean"
                    )

    def _get_shared_namespaces(self) -> List[str]:
        """Return configured shared namespaces.

        Defaults to the legacy ``shared`` namespace when not configured.
        """
        namespaces = self._config.get("shared_namespaces")
        if not namespaces:
            return ["shared"]
        return [str(namespace) for namespace in namespaces]

    def _is_shared_resource(self, resource: str) -> bool:
        """Check whether a resource belongs to a shared namespace."""
        return any(
            resource.startswith(f"{namespace}:")
            for namespace in self._get_shared_namespaces()
        )

    def _match_namespace(self, pattern: str, resource: str, agent_id: str) -> bool:
        """Check if a resource matches a namespace pattern.

        Args:
            pattern: Namespace pattern (e.g., "hermes:*", "${agent_id}:*")
            resource: Resource identifier (e.g., "hermes:memory:123")
            agent_id: Agent identifier

        Returns:
            True if resource matches pattern
        """
        resolved_pattern = pattern.replace("${agent_id}", agent_id)

        if resolved_pattern.endswith(":*"):
            prefix = resolved_pattern[:-2]
            return resource.startswith(prefix + ":")

        return resolved_pattern == resource

    def check_permission(
        self,
        agent_id: str,
        operation: str,
        resource: str,
    ) -> bool:
        """Check if an agent has permission for an operation on a resource.

        Args:
            agent_id: Agent identifier
            operation: Operation type (read, write, delete)
            resource: Resource identifier

        Returns:
            True if permission granted
        """
        agents = self._config.get("agents", {})
        agent_config = agents.get(agent_id)

        if agent_config is None:
            agent_config = agents.get("default")

        if agent_config is None:
            logger.warning(f"No config found for agent: {agent_id}")
            return False

        permissions = agent_config.get("permissions", {})

        if permissions.get("admin", False):
            return True

        allowed_operations = permissions.get("operations", [])
        if operation not in allowed_operations:
            return False

        namespace = permissions.get("namespace", "")
        if self._match_namespace(namespace, resource, agent_id):
            return True

        if permissions.get("shared_read", False) and operation == "read":
            if self._is_shared_resource(resource):
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
