"""Tests for configuration management."""

import os
import pytest
import tempfile
import yaml
from memory_mcp.config import Config, load_config


class TestConfig:
    """Test Config class."""

    def test_default_config(self):
        """Test creating config with default values."""
        config = Config()
        
        assert config.server_host == "0.0.0.0"
        assert config.server_port == 5678
        assert config.redis_host == "localhost"
        assert config.redis_port == 6379
        assert config.redis_password == ""
        assert config.redis_db == 0
        assert config.redis_key_prefix == "memory"

    def test_config_from_dict(self):
        """Test creating config from dictionary."""
        data = {
            "server": {
                "host": "127.0.0.1",
                "port": 9090
            },
            "redis": {
                "host": "redis.example.com",
                "port": 6380,
                "password": "secret",
                "db": 1,
                "key_prefix": "mymemory"
            }
        }
        
        config = Config.from_dict(data)
        
        assert config.server_host == "127.0.0.1"
        assert config.server_port == 9090
        assert config.redis_host == "redis.example.com"
        assert config.redis_port == 6380
        assert config.redis_password == "secret"
        assert config.redis_db == 1
        assert config.redis_key_prefix == "mymemory"

    def test_config_from_dict_partial(self):
        """Test creating config from partial dictionary."""
        data = {
            "server": {
                "port": 3000
            }
        }
        
        config = Config.from_dict(data)
        
        assert config.server_host == "0.0.0.0"  # default
        assert config.server_port == 3000  # custom
        assert config.redis_host == "localhost"  # default

    def test_config_from_yaml_file(self, tmp_path):
        """Test loading config from YAML file."""
        config_data = {
            "server": {"host": "192.168.1.1", "port": 8888},
            "redis": {"host": "myredis", "password": "mypassword"}
        }
        
        config_file = tmp_path / "config.yaml"
        with open(config_file, "w") as f:
            yaml.dump(config_data, f)
        
        config = load_config(str(config_file))
        
        assert config.server_host == "192.168.1.1"
        assert config.server_port == 8888
        assert config.redis_host == "myredis"
        assert config.redis_password == "mypassword"

    def test_config_from_nonexistent_file(self):
        """Test loading config from non-existent file returns defaults."""
        config = load_config("/nonexistent/config.yaml")
        
        assert config.server_host == "0.0.0.0"
        assert config.server_port == 5678


class TestConfigEnvironmentVariables:
    """Test config from environment variables."""

    def test_config_from_env_vars(self, monkeypatch):
        """Test loading config from environment variables."""
        monkeypatch.setenv("SERVER_HOST", "10.0.0.1")
        monkeypatch.setenv("SERVER_PORT", "5000")
        monkeypatch.setenv("REDIS_HOST", "envredis")
        monkeypatch.setenv("REDIS_PORT", "6380")
        monkeypatch.setenv("REDIS_PASSWORD", "envpassword")
        
        config = Config.from_env()
        
        assert config.server_host == "10.0.0.1"
        assert config.server_port == 5000
        assert config.redis_host == "envredis"
        assert config.redis_port == 6380
        assert config.redis_password == "envpassword"

    def test_config_env_vars_override_defaults(self, monkeypatch):
        """Test that environment variables override defaults."""
        monkeypatch.setenv("SERVER_PORT", "9999")
        
        config = Config.from_env()
        
        assert config.server_host == "0.0.0.0"  # default
        assert config.server_port == 9999  # from env


class TestConfigPriority:
    """Test config priority: file < env vars."""

    def test_env_vars_override_file(self, monkeypatch, tmp_path):
        """Test that env vars override file config."""
        config_data = {
            "server": {"host": "filehost", "port": 1111},
            "redis": {"host": "fileredis"}
        }
        
        config_file = tmp_path / "config.yaml"
        with open(config_file, "w") as f:
            yaml.dump(config_data, f)
        
        monkeypatch.setenv("SERVER_HOST", "envhost")
        monkeypatch.setenv("SERVER_PORT", "2222")
        
        config = load_config(str(config_file), use_env=True)
        
        assert config.server_host == "envhost"  # env overrides file
        assert config.server_port == 2222  # env overrides file
        assert config.redis_host == "fileredis"  # file value kept
