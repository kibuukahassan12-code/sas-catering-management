"""
Safe Migration Script for Event Service Department Schema

This script synchronizes the service_events table and related tables
with the authoritative ServiceEvent model definition.

DO NOT run this automatically - it must be run manually after verification.
"""
import os
import sys
import sqlite3
from pathlib import Path

# Add parent directory to path for imports
BASE_DIR = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(BASE_DIR))

# Database path candidates
DB_CANDIDATES = [
    os.path.join("sas_management", "instance", "sas.db"),
    os.path.join("sas_management", "instance", "site.db"),
    os.path.join("instance", "sas.db"),
    os.path.join("instance", "site.db"),
    "sas.db",
    "site.db"
]

def find_database():
    """Find the database file."""
    for db_path in DB_CANDIDATES:
        if os.path.exists(db_path):
            return db_path
    return None

def get_existing_columns(cursor, table_name):
    """Get list of existing column names in a table."""
    try:
        cursor.execute(f"PRAGMA table_info({table_name})")
        return [row[1] for row in cursor.fetchall()]
    except Exception as e:
        print(f"[ERROR] Could not get columns for {table_name}: {e}")
        return []

def add_column_safe(cursor, conn, table_name, column_name, column_type, default_value=None):
    """Safely add a column to a table if it doesn't exist."""
    existing = get_existing_columns(cursor, table_name)
    
    if column_name in existing:
        print(f"[SKIP] {table_name}.{column_name} already exists")
        return False
    
    try:
        sql = f"ALTER TABLE {table_name} ADD COLUMN {column_name} {column_type}"
        if default_value is not None:
            if isinstance(default_value, str):
                sql += f" DEFAULT '{default_value}'"
            else:
                sql += f" DEFAULT {default_value}"
        
        cursor.execute(sql)
        conn.commit()
        print(f"[ADD] {table_name}.{column_name} ({column_type})")
        return True
    except sqlite3.OperationalError as e:
        error_msg = str(e).lower()
        if "duplicate column" in error_msg or "already exists" in error_msg:
            print(f"[SKIP] {table_name}.{column_name} already exists (detected during add)")
            return False
        else:
            print(f"[ERROR] Failed to add {table_name}.{column_name}: {e}")
            conn.rollback()
            return False
    except Exception as e:
        print(f"[ERROR] Unexpected error adding {table_name}.{column_name}: {e}")
        conn.rollback()
        return False

def create_table_if_not_exists(cursor, conn, table_name, create_sql):
    """Create a table if it doesn't exist."""
    try:
        cursor.execute(f"SELECT name FROM sqlite_master WHERE type='table' AND name='{table_name}'")
        if cursor.fetchone():
            print(f"[SKIP] Table {table_name} already exists")
            return False
        
        cursor.execute(create_sql)
        conn.commit()
        print(f"[CREATE] Table {table_name}")
        return True
    except Exception as e:
        print(f"[ERROR] Failed to create {table_name}: {e}")
        conn.rollback()
        return False

def migrate_service_events_schema():
    """Main migration function."""
    db_path = find_database()
    
    if not db_path:
        print("[ERROR] Database not found. Tried:")
        for candidate in DB_CANDIDATES:
            print(f"  - {candidate}")
        print("\nPlease ensure the database exists before running this migration.")
        return False
    
    print(f"[INFO] Using database: {db_path}")
    print("[INFO] Starting Event Service Department schema migration...\n")
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # Check if service_events table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='service_events'")
        table_exists = cursor.fetchone() is not None
        
        if not table_exists:
            print("[WARN] service_events table does not exist.")
            print("[INFO] Table will be created by SQLAlchemy on app startup.")
            print("[INFO] Run this migration again after the table is created.\n")
            # Still create supporting tables
        else:
            print("[INFO] service_events table exists. Checking columns...\n")
            
            # Define required columns for service_events based on ServiceEvent model
            service_events_columns = [
                ("title", "TEXT NOT NULL", None),
                ("event_type", "TEXT", None),
                ("client_id", "INTEGER", None),
                ("event_date", "DATE", None),
                ("venue", "TEXT", None),
                ("guest_count", "INTEGER", None),
                ("status", "TEXT NOT NULL", "Planned"),
                ("notes", "TEXT", None),
                ("created_at", "DATETIME NOT NULL", None),
                ("updated_at", "DATETIME NOT NULL", None),
            ]
            
            # Add missing columns
            for col_name, col_type, default_val in service_events_columns:
                add_column_safe(cursor, conn, "service_events", col_name, col_type, default_val)
        
        print()
        
        # Ensure service_event_items table exists with correct schema
        print("[INFO] Checking service_event_items table...")
        create_table_if_not_exists(cursor, conn, "service_event_items", """
            CREATE TABLE service_event_items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                service_event_id INTEGER NOT NULL,
                item_name TEXT NOT NULL,
                category TEXT,
                quantity INTEGER NOT NULL DEFAULT 1,
                unit_cost NUMERIC(12,2) NOT NULL DEFAULT 0.00,
                total_cost NUMERIC(12,2) NOT NULL DEFAULT 0.00,
                created_at DATETIME NOT NULL,
                updated_at DATETIME NOT NULL,
                FOREIGN KEY (service_event_id) REFERENCES service_events(id) ON DELETE CASCADE
            )
        """)
        
        # Add missing columns to service_event_items if table exists
        if cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='service_event_items'").fetchone():
            items_columns = [
                ("service_event_id", "INTEGER NOT NULL", None),
                ("item_name", "TEXT NOT NULL", None),
                ("category", "TEXT", None),
                ("quantity", "INTEGER NOT NULL", 1),
                ("unit_cost", "NUMERIC(12,2) NOT NULL", 0.00),
                ("total_cost", "NUMERIC(12,2) NOT NULL", 0.00),
                ("created_at", "DATETIME NOT NULL", None),
                ("updated_at", "DATETIME NOT NULL", None),
            ]
            for col_name, col_type, default_val in items_columns:
                add_column_safe(cursor, conn, "service_event_items", col_name, col_type, default_val)
        
        print()
        
        # Ensure service_staff_assignments table exists with correct schema
        print("[INFO] Checking service_staff_assignments table...")
        create_table_if_not_exists(cursor, conn, "service_staff_assignments", """
            CREATE TABLE service_staff_assignments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                service_event_id INTEGER NOT NULL,
                staff_id INTEGER,
                role TEXT,
                shift TEXT,
                notes TEXT,
                created_at DATETIME NOT NULL,
                FOREIGN KEY (service_event_id) REFERENCES service_events(id) ON DELETE CASCADE,
                FOREIGN KEY (staff_id) REFERENCES user(id)
            )
        """)
        
        # Add missing columns to service_staff_assignments if table exists
        if cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='service_staff_assignments'").fetchone():
            staff_columns = [
                ("service_event_id", "INTEGER NOT NULL", None),
                ("staff_id", "INTEGER", None),
                ("role", "TEXT", None),
                ("shift", "TEXT", None),
                ("notes", "TEXT", None),
                ("created_at", "DATETIME NOT NULL", None),
            ]
            for col_name, col_type, default_val in staff_columns:
                add_column_safe(cursor, conn, "service_staff_assignments", col_name, col_type, default_val)
        
        print()
        
        # Ensure service_checklist_items table exists with correct schema
        print("[INFO] Checking service_checklist_items table...")
        create_table_if_not_exists(cursor, conn, "service_checklist_items", """
            CREATE TABLE service_checklist_items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                service_event_id INTEGER NOT NULL,
                stage TEXT,
                description TEXT NOT NULL,
                completed INTEGER NOT NULL DEFAULT 0,
                created_at DATETIME NOT NULL,
                updated_at DATETIME NOT NULL,
                FOREIGN KEY (service_event_id) REFERENCES service_events(id) ON DELETE CASCADE
            )
        """)
        
        # Add missing columns to service_checklist_items if table exists
        if cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='service_checklist_items'").fetchone():
            checklist_columns = [
                ("service_event_id", "INTEGER NOT NULL", None),
                ("stage", "TEXT", None),
                ("description", "TEXT NOT NULL", None),
                ("completed", "INTEGER NOT NULL", 0),
                ("created_at", "DATETIME NOT NULL", None),
                ("updated_at", "DATETIME NOT NULL", None),
            ]
            for col_name, col_type, default_val in checklist_columns:
                add_column_safe(cursor, conn, "service_checklist_items", col_name, col_type, default_val)
        
        print()
        print("[SUCCESS] Event Service Department schema migration completed!")
        print("[INFO] Please restart the application to verify the changes.")
        
        return True
        
    except Exception as e:
        print(f"\n[ERROR] Migration failed: {e}")
        conn.rollback()
        return False
    finally:
        conn.close()

if __name__ == "__main__":
    success = migrate_service_events_schema()
    sys.exit(0 if success else 1)

