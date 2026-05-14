"""Authentication middleware for Memory MCP Server.

This module provides API key authentication for the REST API.
"""

import logging
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class AuthMiddleware:
    """API Key authentication middleware."""

    def __init__(self, config: Dict[str, Any]):
        """Initialize auth middleware.
        
        Args:
            config: Authentication configuration with api_keys list
        """
        self._api_keys: List[str] = config.get("api_keys", [])
        self._api_key_store = config.get("api_key_store")
        self._acl = config.get("acl")

    def validate_api_key(self, api_key: Optional[str]) -> bool:
        """Validate an API key."""
        if self._api_key_store is not None:
            if not self._api_key_store.is_enforced():
                return True
            return self._api_key_store.validate_key(api_key)

        if not self._api_keys:
            return True
        if not api_key:
            return False
        return api_key in self._api_keys

    def record_usage(self, api_key: Optional[str]) -> None:
        """Record successful usage for a managed API key."""
        if self._api_key_store is not None:
            self._api_key_store.record_usage(api_key)

    def extract_api_key(
        self,
        headers: Dict[str, str],
        query_params: Optional[Dict[str, str]] = None
    ) -> Optional[str]:
        """Extract API key from request.
        
        Args:
            headers: Request headers
            query_params: Query parameters
            
        Returns:
            API key if found, None otherwise
        """
        # Try Authorization header (Bearer token)
        auth_header = headers.get("authorization", "")
        if auth_header.startswith("Bearer "):
            return auth_header[7:]
        
        # Try X-API-Key header
        api_key_header = headers.get("x-api-key")
        if api_key_header:
            return api_key_header
        
        # Try query parameter
        if query_params:
            api_key_query = query_params.get("api_key")
            if api_key_query:
                return api_key_query
        
        return None
