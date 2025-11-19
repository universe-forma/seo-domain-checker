import os
import sqlite3
import threading
from functools import wraps
from sqlite3 import Connection

from alembic import command
from alembic.config import Config
from enum import Enum


class LinkDirection(str, Enum):
    IN = "in"
    OUT = "out"


# Use environment variable if set (for Docker), otherwise use default
project_root = os.path.abspath(os.getcwd())
DB_PATH = os.environ.get("DB_PATH", os.path.join(project_root, "ahrefs_data.db"))

_thread_local = threading.local()
_db_initialized = False
_db_path: str = ""


def init_database(db_path: str = DB_PATH, alembic_ini_path: str = "alembic.ini"):
    if not db_path:
        raise RuntimeError("Database not configured. Provide db_path during initialization.")
    alembic_cfg = Config(alembic_ini_path)
    db_url = f"sqlite:///{db_path}"
    print(alembic_cfg.get_alembic_option("script_location"))
    alembic_cfg.set_main_option("sqlalchemy.url", db_url)
    command.upgrade(alembic_cfg, "head")
    global _db_path
    _db_path = db_path
    global _db_initialized
    _db_initialized = True
    print("Initialized database.")


def get_thread_connection() -> Connection:
    if not _db_initialized:
        raise RuntimeError("Database not initialized.")
    conn = getattr(_thread_local, "conn", None)
    if conn is None:
        conn = sqlite3.connect(_db_path)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        _thread_local.conn = conn
    return conn


def persist_domain_categories(conn: Connection, target_id: str, domain_categories):
    try:
        cur = conn.cursor()
        for domain, category in domain_categories.items():
            update_query = """
                            UPDATE batch_analysis SET domain_category = ? WHERE target_id = ? AND domain = ?
                        """

            values = (
                category,
                target_id,
                domain
            )
            cur.execute(update_query, values)
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()
