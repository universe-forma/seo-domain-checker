#!/usr/bin/env python3
"""
Database initialization script
Runs automatically on container startup to ensure database schema exists
"""
import os
import sqlite3
import sys

# Use environment variable if set (for Docker), otherwise use default
DB_PATH = os.environ.get("DB_PATH", "/app/ahrefs_data.db")
SCHEMA_PATH = "/app/ddl/001-initial-schema.sql"

# Ensure the database directory exists
db_dir = os.path.dirname(DB_PATH)
if db_dir and not os.path.exists(db_dir):
    os.makedirs(db_dir, exist_ok=True)
    print(f"📁 Created database directory: {db_dir}")

def init_database():
    """Initialize database with schema if tables don't exist"""
    try:
        print("🔍 Checking database status...")
        
        # Check if database exists and has tables
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # Check if analysis table exists (main table)
        cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='analysis'"
        )
        
        if cursor.fetchone() is None:
            print("📊 Database tables not found. Creating schema...")
            
            # Read and execute schema
            if not os.path.exists(SCHEMA_PATH):
                print(f"❌ Schema file not found at {SCHEMA_PATH}", file=sys.stderr)
                conn.close()
                return False
            
            with open(SCHEMA_PATH, 'r') as f:
                schema_sql = f.read()
            
            conn.executescript(schema_sql)
            conn.commit()
            print("✅ Database schema created successfully!")
            
            # Verify tables were created
            cursor.execute(
                "SELECT COUNT(*) FROM sqlite_master WHERE type='table'"
            )
            table_count = cursor.fetchone()[0]
            print(f"✅ Created {table_count} tables")
        else:
            print("✅ Database tables already exist. Skipping initialization.")
        
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Error initializing database: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = init_database()
    sys.exit(0 if success else 1)

