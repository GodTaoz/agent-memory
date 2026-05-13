"""Configuration management for Memory MCP Server."""

import os
from dataclasses import dataclass, field
from typing import Any, Dict, Optional

import yaml


@dataclass
class Config:
    """Application configuration."""
    
    # Server settings
    server_host: str = "0.0.0.0"
    server_port: int = 5678
    server_workers: int = 1
    
    # Redis settings
    redis_host: str = "localhost"
    redis_port: int = 6379
    redis_password: str = ""
    redis_db: int = 0
    redis_key_prefix: str = "memory"
    
    # Memory settings
    max_content_length: int = 10000
    similarity_threshold: float = 0.3
    max_tags: int = 20
    
    # Search settings
    max_results: int = 100
    enable_synonyms: bool = True
    enable_fuzzy: bool = True
    
    # Logging
    log_level: str = "INFO"
    log_format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Config":
        """Create config from dictionary."""
        config = cls()
        
        # Server settings
        server = data.get("server", {})
        config.server_host = server.get("host", config.server_host)
        config.server_port = server.get("port", config.server_port)
        config.server_workers = server.get("workers", config.server_workers)
        
        # Redis settings
        redis = data.get("redis", {})
        config.redis_host = redis.get("host", config.redis_host)
        config.redis_port = redis.get("port", config.redis_port)
        config.redis_password = redis.get("password", config.redis_password)
        config.redis_db = redis.get("db", config.redis_db)
        config.redis_key_prefix = redis.get("key_prefix", config.redis_key_prefix)
        
        # Memory settings
        memory = data.get("memory", {})
        config.max_content_length = memory.get("max_content_length", config.max_content_length)
        config.similarity_threshold = memory.get("similarity_threshold", config.similarity_threshold)
        config.max_tags = memory.get("max_tags", config.max_tags)
        
        # Search settings
        search = data.get("search", {})
        config.max_results = search.get("max_results", config.max_results)
        config.enable_synonyms = search.get("enable_synonyms", config.enable_synonyms)
        config.enable_fuzzy = search.get("enable_fuzzy", config.enable_fuzzy)
        
        # Logging
        logging_config = data.get("logging", {})
        config.log_level = logging_config.get("level", config.log_level)
        config.log_format = logging_config.get("format", config.log_format)
        
        return config

    @classmethod
    def from_env(cls) -> "Config":
        """Create config from environment variables."""
        config = cls()
        
        # Server settings
        config.server_host = os.environ.get("SERVER_HOST", config.server_host)
        config.server_port = int(os.environ.get("SERVER_PORT", config.server_port))
        
        # Redis settings
        config.redis_host = os.environ.get("REDIS_HOST", config.redis_host)
        config.redis_port = int(os.environ.get("REDIS_PORT", config.redis_port))
        config.redis_password = os.environ.get("REDIS_PASSWORD", config.redis_password)
        config.redis_db = int(os.environ.get("REDIS_DB", config.redis_db))
        
        # Logging
        config.log_level = os.environ.get("LOG_LEVEL", config.log_level)
        
        return config

    def to_dict(self) -> Dict[str, Any]:
        """Convert config to dictionary."""
        return {
            "server": {
                "host": self.server_host,
                "port": self.server_port,
                "workers": self.server_workers
            },
            "redis": {
                "host": self.redis_host,
                "port": self.redis_port,
                "password": self.redis_password,
                "db": self.redis_db,
                "key_prefix": self.redis_key_prefix
            },
            "memory": {
                "max_content_length": self.max_content_length,
                "similarity_threshold": self.similarity_threshold,
                "max_tags": self.max_tags
            },
            "search": {
                "max_results": self.max_results,
                "enable_synonyms": self.enable_synonyms,
                "enable_fuzzy": self.enable_fuzzy
            },
            "logging": {
                "level": self.log_level,
                "format": self.log_format
            }
        }


def load_config(config_path: Optional[str] = None, use_env: bool = False) -> Config:
    """Load configuration from file and/or environment variables.
    
    Priority: environment variables > config file > defaults
    """
    config = Config()
    
    # Load from file if provided
    if config_path and os.path.exists(config_path):
        try:
            with open(config_path, "r") as f:
                data = yaml.safe_load(f) or {}
            config = Config.from_dict(data)
        except Exception:
            pass  # Use defaults if file is invalid
    
    # Override with environment variables if requested
    if use_env:
        env_config = Config.from_env()
        # Only override if env var is explicitly set
        if "SERVER_HOST" in os.environ:
            config.server_host = env_config.server_host
        if "SERVER_PORT" in os.environ:
            config.server_port = env_config.server_port
        if "REDIS_HOST" in os.environ:
            config.redis_host = env_config.redis_host
        if "REDIS_PORT" in os.environ:
            config.redis_port = env_config.redis_port
        if "REDIS_PASSWORD" in os.environ:
            config.redis_password = env_config.redis_password
        if "REDIS_DB" in os.environ:
            config.redis_db = env_config.redis_db
        if "LOG_LEVEL" in os.environ:
            config.log_level = env_config.log_level
    
    return config
