#!/usr/bin/env python3
"""
Database initialization script
Runs automatically on container startup to ensure database schema exists
Supports both SQLite and PostgreSQL
"""
import os
import sys

# Determine database type
DB_TYPE = os.environ.get("DB_TYPE", "sqlite").lower()

if DB_TYPE == "postgresql":
    try:
        import psycopg2
        import psycopg2.extras
    except ImportError:
        print("❌ PostgreSQL support not available. Install psycopg2-binary", file=sys.stderr)
        sys.exit(1)
else:
    import sqlite3


def init_sqlite_database():
    """Initialize SQLite database with schema if tables don't exist"""
    DB_PATH = os.environ.get("SQLITE_DB_PATH", "/app/ahrefs_data.db")
    SCHEMA_PATH = "/app/ddl/001-initial-schema.sql"
    
    try:
        print("🔍 Checking SQLite database status...")
        
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # Check if analysis table exists
        cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='analysis'"
        )
        
        if cursor.fetchone() is None:
            print("📊 Database tables not found. Creating schema...")
            
            if not os.path.exists(SCHEMA_PATH):
                print(f"❌ Schema file not found at {SCHEMA_PATH}", file=sys.stderr)
                conn.close()
                return False
            
            with open(SCHEMA_PATH, 'r') as f:
                schema_sql = f.read()
            
            conn.executescript(schema_sql)
            conn.commit()
            print("✅ SQLite schema created successfully!")
            
            # Verify tables were created
            cursor.execute(
                "SELECT COUNT(*) FROM sqlite_master WHERE type='table'"
            )
            table_count = cursor.fetchone()[0]
            print(f"✅ Created {table_count} tables")
        else:
            print("✅ SQLite tables already exist. Skipping initialization.")
        
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Error initializing SQLite database: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        return False


def init_postgresql_database():
    """Initialize PostgreSQL database with schema if tables don't exist"""
    import psycopg2
    from psycopg2 import sql
    
    # Get connection parameters from environment
    # Support both POSTGRES_* and DB_* naming conventions
    DB_HOST = os.environ.get("POSTGRES_HOST") or os.environ.get("DB_HOST", "localhost")
    DB_PORT = os.environ.get("POSTGRES_PORT") or os.environ.get("DB_PORT", "5432")
    DB_NAME = os.environ.get("POSTGRES_DB") or os.environ.get("DB_NAME", "seo_checker")
    DB_USER = os.environ.get("POSTGRES_USER") or os.environ.get("DB_USER", "postgres")
    DB_PASSWORD = os.environ.get("POSTGRES_PASSWORD") or os.environ.get("DB_PASSWORD", "password")
    
    try:
        print(f"🔍 Connecting to PostgreSQL at {DB_HOST}:{DB_PORT}/{DB_NAME}...")
        
        conn = psycopg2.connect(
            host=DB_HOST,
            port=DB_PORT,
            database=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD
        )
        conn.autocommit = True
        cursor = conn.cursor()
        
        # Check if analysis table exists
        cursor.execute("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_schema = 'public' 
                AND table_name = 'analysis'
            )
        """)
        
        table_exists = cursor.fetchone()[0]
        
        if not table_exists:
            print("📊 Database tables not found. Creating PostgreSQL schema...")
            
            # Read and convert SQLite schema to PostgreSQL
            SCHEMA_PATH = "/app/ddl/001-initial-schema.sql"
            
            if not os.path.exists(SCHEMA_PATH):
                print(f"❌ Schema file not found at {SCHEMA_PATH}", file=sys.stderr)
                conn.close()
                return False
            
            with open(SCHEMA_PATH, 'r') as f:
                schema_sql = f.read()
            
            # Convert SQLite schema to PostgreSQL
            # Remove SQLite-specific pragmas
            schema_sql = schema_sql.replace("PRAGMA foreign_keys = ON;", "")
            
            # Convert SQLite types to PostgreSQL types
            schema_sql = schema_sql.replace("INTEGER", "INT")
            schema_sql = schema_sql.replace("REAL", "NUMERIC")
            schema_sql = schema_sql.replace("TIMESTAMP DEFAULT CURRENT_TIMESTAMP", 
                                           "TIMESTAMP DEFAULT CURRENT_TIMESTAMP")
            
            # Execute schema
            cursor.execute(schema_sql)
            print("✅ PostgreSQL schema created successfully!")
            
            # Verify tables were created
            cursor.execute("""
                SELECT COUNT(*) FROM information_schema.tables 
                WHERE table_schema = 'public'
            """)
            table_count = cursor.fetchone()[0]
            print(f"✅ Created {table_count} tables")
        else:
            print("✅ PostgreSQL tables already exist. Skipping initialization.")
        
        cursor.close()
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Error initializing PostgreSQL database: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        return False


def init_database():
    """Initialize database based on DB_TYPE environment variable"""
    print(f"🚀 Database initialization started (Type: {DB_TYPE})")
    
    if DB_TYPE == "postgresql":
        success = init_postgresql_database()
    else:
        success = init_sqlite_database()
    
    if success:
        print("✅ Database initialization completed successfully!")
    else:
        print("❌ Database initialization failed!", file=sys.stderr)
    
    return success


if __name__ == "__main__":
    success = init_database()
    sys.exit(0 if success else 1)
