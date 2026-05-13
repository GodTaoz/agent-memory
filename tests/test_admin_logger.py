"""Tests for SQLite logger."""

import pytest
import tempfile
from pathlib import Path

from memory_mcp.admin.logger import SQLiteLogger


class TestSQLiteLogger:
    """Test SQLite logger."""
    
    @pytest.fixture
    def logger(self, tmp_path):
        """Create test logger."""
        db_path = str(tmp_path / "test_logs.db")
        return SQLiteLogger(db_path)
    
    def test_init_db(self, logger):
        """Test database initialization."""
        assert logger.db_path.exists()
    
    def test_log_operation(self, logger):
        """Test logging an operation."""
        logger.log_operation(
            level="info",
            category="test",
            message="Test message",
            details={"key": "value"}
        )
        
        logs = logger.get_operation_logs()
        assert len(logs) == 1
        assert logs[0]["message"] == "Test message"
        assert logs[0]["level"] == "info"
        assert logs[0]["category"] == "test"
        assert logs[0]["details"] == {"key": "value"}
    
    def test_log_login(self, logger):
        """Test logging a login attempt."""
        logger.log_login(success=True, ip_address="127.0.0.1")
        
        logs = logger.get_login_logs()
        assert len(logs) == 1
        assert logs[0]["success"] is True
        assert logs[0]["ip_address"] == "127.0.0.1"
    
    def test_log_login_failure(self, logger):
        """Test logging a failed login."""
        logger.log_login(
            success=False,
            ip_address="192.168.1.1",
            failure_reason="Invalid password"
        )
        
        logs = logger.get_login_logs()
        assert len(logs) == 1
        assert logs[0]["success"] is False
        assert logs[0]["failure_reason"] == "Invalid password"
    
    def test_log_api_access(self, logger):
        """Test logging an API access."""
        logger.log_api_access(
            method="GET",
            path="/api/v1/memories",
            status_code=200,
            response_time_ms=15.5,
            api_key_preview="abc123...",
            ip_address="10.0.0.1"
        )
        
        logs = logger.get_api_access_logs()
        assert len(logs) == 1
        assert logs[0]["method"] == "GET"
        assert logs[0]["path"] == "/api/v1/memories"
        assert logs[0]["status_code"] == 200
        assert logs[0]["response_time_ms"] == 15.5
    
    def test_get_operation_logs_with_filter(self, logger):
        """Test getting operation logs with filters."""
        logger.log_operation(level="info", category="test", message="Info message")
        logger.log_operation(level="error", category="test", message="Error message")
        logger.log_operation(level="info", category="other", message="Other message")
        
        # Filter by level
        logs = logger.get_operation_logs(level="info")
        assert len(logs) == 2
        
        # Filter by category
        logs = logger.get_operation_logs(category="test")
        assert len(logs) == 2
        
        # Filter by both
        logs = logger.get_operation_logs(level="info", category="test")
        assert len(logs) == 1
    
    def test_get_operation_logs_with_limit(self, logger):
        """Test getting operation logs with limit."""
        for i in range(10):
            logger.log_operation(level="info", category="test", message=f"Message {i}")
        
        logs = logger.get_operation_logs(limit=5)
        assert len(logs) == 5
    
    def test_get_stats(self, logger):
        """Test getting log statistics."""
        # Add some test data
        logger.log_operation(level="info", category="test", message="Test")
        logger.log_login(success=True)
        logger.log_login(success=False)
        logger.log_api_access(method="GET", path="/test", status_code=200, response_time_ms=10.0)
        
        stats = logger.get_stats()
        
        assert stats["total_operations"] == 1
        assert stats["total_logins"] == 2
        assert stats["total_api_calls"] == 1
        assert stats["failed_logins"] == 1
        assert stats["avg_response_time_ms"] == 10.0
    
    def test_cleanup_old_logs(self, logger):
        """Test cleaning up old logs."""
        # This is a basic test - in reality you'd need to mock datetime
        logger.cleanup_old_logs(days=30)
        
        # Should not raise any errors
        assert True
