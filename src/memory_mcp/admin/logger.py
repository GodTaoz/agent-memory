"""SQLite logger for operation logs."""

import sqlite3
import json
import os
from datetime import datetime, timedelta
from typing import Optional
from pathlib import Path


def get_config() -> dict:
    """Get admin configuration."""
    return {
        "admin": {
            "log_db_path": os.environ.get("ADMIN_LOG_DB_PATH", "data/admin_logs.db"),
        }
    }


class SQLiteLogger:
    """SQLite-based operation logger."""
    
    def __init__(self, db_path: Optional[str] = None):
        if db_path is None:
            config = get_config()
            admin_config = config.get("admin", {})
            db_path = admin_config.get("log_db_path", "data/admin_logs.db")
        
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()
    
    def _init_db(self):
        """Initialize database tables."""
        with sqlite3.connect(str(self.db_path)) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS operation_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    level TEXT NOT NULL,
                    category TEXT NOT NULL,
                    message TEXT NOT NULL,
                    details TEXT,
                    ip_address TEXT,
                    user_agent TEXT,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            conn.execute("""
                CREATE TABLE IF NOT EXISTS login_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    success BOOLEAN NOT NULL,
                    ip_address TEXT,
                    user_agent TEXT,
                    failure_reason TEXT,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            conn.execute("""
                CREATE TABLE IF NOT EXISTS api_access_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    method TEXT NOT NULL,
                    path TEXT NOT NULL,
                    status_code INTEGER,
                    response_time_ms REAL,
                    api_key_preview TEXT,
                    ip_address TEXT,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Create indexes
            conn.execute("CREATE INDEX IF NOT EXISTS idx_logs_timestamp ON operation_logs(timestamp)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_logs_level ON operation_logs(level)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_logs_category ON operation_logs(category)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_login_timestamp ON login_logs(timestamp)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_api_timestamp ON api_access_logs(timestamp)")
            
            conn.commit()
    
    def log_operation(
        self,
        level: str,
        category: str,
        message: str,
        details: Optional[dict] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ):
        """Log an operation."""
        with sqlite3.connect(str(self.db_path)) as conn:
            conn.execute(
                """
                INSERT INTO operation_logs (timestamp, level, category, message, details, ip_address, user_agent)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    datetime.now().isoformat(),
                    level,
                    category,
                    message,
                    json.dumps(details) if details else None,
                    ip_address,
                    user_agent
                )
            )
            conn.commit()
    
    def log_login(
        self,
        success: bool,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        failure_reason: Optional[str] = None
    ):
        """Log a login attempt."""
        with sqlite3.connect(str(self.db_path)) as conn:
            conn.execute(
                """
                INSERT INTO login_logs (timestamp, success, ip_address, user_agent, failure_reason)
                VALUES (?, ?, ?, ?, ?)
                """,
                (
                    datetime.now().isoformat(),
                    success,
                    ip_address,
                    user_agent,
                    failure_reason
                )
            )
            conn.commit()
    
    def log_api_access(
        self,
        method: str,
        path: str,
        status_code: int,
        response_time_ms: float,
        api_key_preview: Optional[str] = None,
        ip_address: Optional[str] = None
    ):
        """Log an API access."""
        with sqlite3.connect(str(self.db_path)) as conn:
            conn.execute(
                """
                INSERT INTO api_access_logs (timestamp, method, path, status_code, response_time_ms, api_key_preview, ip_address)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    datetime.now().isoformat(),
                    method,
                    path,
                    status_code,
                    response_time_ms,
                    api_key_preview,
                    ip_address
                )
            )
            conn.commit()
    
    def get_operation_logs(
        self,
        level: Optional[str] = None,
        category: Optional[str] = None,
        limit: int = 100,
        offset: int = 0
    ) -> list[dict]:
        """Get operation logs with filtering."""
        with sqlite3.connect(str(self.db_path)) as conn:
            conn.row_factory = sqlite3.Row
            
            query = "SELECT * FROM operation_logs WHERE 1=1"
            params = []
            
            if level:
                query += " AND level = ?"
                params.append(level)
            
            if category:
                query += " AND category = ?"
                params.append(category)
            
            query += " ORDER BY timestamp DESC LIMIT ? OFFSET ?"
            params.extend([limit, offset])
            
            cursor = conn.execute(query, params)
            rows = cursor.fetchall()
            
            return [
                {
                    "timestamp": row["timestamp"],
                    "level": row["level"],
                    "category": row["category"],
                    "message": row["message"],
                    "details": json.loads(row["details"]) if row["details"] else None,
                    "ip_address": row["ip_address"],
                }
                for row in rows
            ]
    
    def get_login_logs(self, limit: int = 100, offset: int = 0) -> list[dict]:
        """Get login logs."""
        with sqlite3.connect(str(self.db_path)) as conn:
            conn.row_factory = sqlite3.Row
            
            cursor = conn.execute(
                "SELECT * FROM login_logs ORDER BY timestamp DESC LIMIT ? OFFSET ?",
                (limit, offset)
            )
            rows = cursor.fetchall()
            
            return [
                {
                    "timestamp": row["timestamp"],
                    "success": bool(row["success"]),
                    "ip_address": row["ip_address"],
                    "failure_reason": row["failure_reason"],
                }
                for row in rows
            ]
    
    def get_api_access_logs(self, limit: int = 100, offset: int = 0) -> list[dict]:
        """Get API access logs."""
        with sqlite3.connect(str(self.db_path)) as conn:
            conn.row_factory = sqlite3.Row
            
            cursor = conn.execute(
                "SELECT * FROM api_access_logs ORDER BY timestamp DESC LIMIT ? OFFSET ?",
                (limit, offset)
            )
            rows = cursor.fetchall()
            
            return [
                {
                    "timestamp": row["timestamp"],
                    "method": row["method"],
                    "path": row["path"],
                    "status_code": row["status_code"],
                    "response_time_ms": row["response_time_ms"],
                    "api_key_preview": row["api_key_preview"],
                    "ip_address": row["ip_address"],
                }
                for row in rows
            ]
    
    def get_stats(self) -> dict:
        """Get log statistics."""
        with sqlite3.connect(str(self.db_path)) as conn:
            # Total logs
            total_ops = conn.execute("SELECT COUNT(*) FROM operation_logs").fetchone()[0]
            total_logins = conn.execute("SELECT COUNT(*) FROM login_logs").fetchone()[0]
            total_api = conn.execute("SELECT COUNT(*) FROM api_access_logs").fetchone()[0]
            
            # Today's logs
            today = datetime.now().date().isoformat()
            today_ops = conn.execute(
                "SELECT COUNT(*) FROM operation_logs WHERE timestamp LIKE ?",
                (f"{today}%",)
            ).fetchone()[0]
            today_api = conn.execute(
                "SELECT COUNT(*) FROM api_access_logs WHERE timestamp LIKE ?",
                (f"{today}%",)
            ).fetchone()[0]
            
            # Failed logins
            failed_logins = conn.execute(
                "SELECT COUNT(*) FROM login_logs WHERE success = 0"
            ).fetchone()[0]
            
            # Average response time
            avg_response = conn.execute(
                "SELECT AVG(response_time_ms) FROM api_access_logs"
            ).fetchone()[0] or 0
            
            return {
                "total_operations": total_ops,
                "total_logins": total_logins,
                "total_api_calls": total_api,
                "today_operations": today_ops,
                "today_api_calls": today_api,
                "failed_logins": failed_logins,
                "avg_response_time_ms": round(avg_response, 2),
            }
    
    def cleanup_old_logs(self, days: int = 30):
        """Delete logs older than specified days."""
        cutoff = datetime.now().replace(hour=0, minute=0, second=0)
        cutoff = cutoff - timedelta(days=days)
        cutoff_str = cutoff.isoformat()
        
        with sqlite3.connect(str(self.db_path)) as conn:
            conn.execute("DELETE FROM operation_logs WHERE timestamp < ?", (cutoff_str,))
            conn.execute("DELETE FROM login_logs WHERE timestamp < ?", (cutoff_str,))
            conn.execute("DELETE FROM api_access_logs WHERE timestamp < ?", (cutoff_str,))
            conn.commit()


# Singleton instance
_logger: Optional[SQLiteLogger] = None


def get_logger() -> SQLiteLogger:
    """Get singleton logger instance."""
    global _logger
    if _logger is None:
        _logger = SQLiteLogger()
    return _logger
