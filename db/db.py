import os
import sqlite3
import threading
from functools import wraps
from typing import Union, Any
from enum import Enum

from alembic import command
from alembic.config import Config

try:
    import psycopg2
    import psycopg2.extras
    POSTGRES_AVAILABLE = True
except ImportError:
    POSTGRES_AVAILABLE = False


class LinkDirection(str, Enum):
    IN = "in"
    OUT = "out"


class DatabaseType(str, Enum):
    SQLITE = "sqlite"
    POSTGRESQL = "postgresql"


# Database configuration from environment variables
# Support both DB_* and POSTGRES_* naming conventions
DB_TYPE = os.environ.get("DB_TYPE", "sqlite").lower()

# PostgreSQL configuration - support POSTGRES_* variables (preferred by DevOps)
DB_HOST = os.environ.get("POSTGRES_HOST") or os.environ.get("DB_HOST", "localhost")
DB_PORT = os.environ.get("POSTGRES_PORT") or os.environ.get("DB_PORT", "5432")
DB_NAME = os.environ.get("POSTGRES_DB") or os.environ.get("DB_NAME", "seo_checker")
DB_USER = os.environ.get("POSTGRES_USER") or os.environ.get("DB_USER", "postgres")
DB_PASSWORD = os.environ.get("POSTGRES_PASSWORD") or os.environ.get("DB_PASSWORD", "password")
DATABASE_URL = os.environ.get("DATABASE_URL")

# SQLite fallback
project_root = os.path.abspath(os.getcwd())
SQLITE_DB_PATH = os.environ.get("SQLITE_DB_PATH", os.path.join(project_root, "ahrefs_data.db"))

_thread_local = threading.local()
_db_initialized = False
_db_type: DatabaseType = DatabaseType.SQLITE
_connection_params = {}


def get_database_url() -> str:
    """Get database URL based on configuration"""
    if DATABASE_URL:
        return DATABASE_URL
    
    if DB_TYPE == "postgresql":
        return f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
    else:
        return f"sqlite:///{SQLITE_DB_PATH}"


def init_database(db_url: str = None, alembic_ini_path: str = "alembic.ini"):
    """Initialize database with Alembic migrations"""
    global _db_initialized, _db_type, _connection_params
    
    if not db_url:
        db_url = get_database_url()
    
    print(f"🔍 Initializing database: {db_url.split('@')[0] if '@' in db_url else db_url}")
    
    # Determine database type
    if db_url.startswith("postgresql"):
        _db_type = DatabaseType.POSTGRESQL
        if not POSTGRES_AVAILABLE:
            raise RuntimeError("PostgreSQL support not available. Install psycopg2-binary")
        
        # Parse connection parameters
        # Format: postgresql://user:password@host:port/dbname
        parts = db_url.replace("postgresql://", "").split("@")
        if len(parts) == 2:
            user_pass = parts[0].split(":")
            host_port_db = parts[1].split("/")
            host_port = host_port_db[0].split(":")
            
            _connection_params = {
                "host": host_port[0],
                "port": int(host_port[1]) if len(host_port) > 1 else 5432,
                "database": host_port_db[1] if len(host_port_db) > 1 else DB_NAME,
                "user": user_pass[0] if len(user_pass) > 0 else DB_USER,
                "password": user_pass[1] if len(user_pass) > 1 else DB_PASSWORD
            }
    else:
        _db_type = DatabaseType.SQLITE
        _connection_params = {"database": db_url.replace("sqlite:///", "")}
    
    # Run Alembic migrations
    try:
        alembic_cfg = Config(alembic_ini_path)
        print(f"📊 Alembic script location: {alembic_cfg.get_alembic_option('script_location')}")
        alembic_cfg.set_main_option("sqlalchemy.url", db_url)
        command.upgrade(alembic_cfg, "head")
        print("✅ Alembic migrations completed")
    except Exception as e:
        print(f"⚠️  Alembic migrations failed (this is OK for first run): {e}")
    
    _db_initialized = True
    print(f"✅ Database initialized ({_db_type.value})")


def get_thread_connection() -> Union[sqlite3.Connection, Any]:
    """Get database connection for current thread"""
    if not _db_initialized:
        raise RuntimeError("Database not initialized. Call init_database() first.")
    
    conn = getattr(_thread_local, "conn", None)
    
    if conn is None:
        if _db_type == DatabaseType.POSTGRESQL:
            conn = psycopg2.connect(**_connection_params)
            conn.autocommit = False
            # Use RealDictCursor for dict-like row access
            _thread_local.cursor_factory = psycopg2.extras.RealDictCursor
        else:
            conn = sqlite3.connect(_connection_params["database"])
            conn.row_factory = sqlite3.Row
            conn.execute("PRAGMA foreign_keys = ON")
        
        _thread_local.conn = conn
    
    return conn


def get_cursor(conn):
    """Get cursor with appropriate row factory"""
    if _db_type == DatabaseType.POSTGRESQL:
        return conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    else:
        return conn.cursor()


def close_thread_connection():
    """Close database connection for current thread"""
    conn = getattr(_thread_local, "conn", None)
    if conn:
        conn.close()
        _thread_local.conn = None


def persist_domain_categories(conn, target_id: str, domain_categories):
    """Persist domain categories to database"""
    try:
        cur = get_cursor(conn)
        for domain, category in domain_categories.items():
            if _db_type == DatabaseType.POSTGRESQL:
                update_query = """
                    UPDATE batch_analysis 
                    SET domain_category = %s 
                    WHERE target_id = %s AND domain = %s
                """
            else:
                update_query = """
                    UPDATE batch_analysis 
                    SET domain_category = ? 
                    WHERE target_id = ? AND domain = ?
                """
            
            values = (category, target_id, domain)
            cur.execute(update_query, values)
        
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        if _db_type == DatabaseType.SQLITE:
            conn.close()


# Compatibility with existing code
DB_PATH = SQLITE_DB_PATH
