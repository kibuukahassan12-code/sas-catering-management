"""
Safe Auto-Fix Script for service_events.event_type Column

This script safely adds the missing 'event_type' column to service_events table.
Designed to run on app startup to fix production schema issues.

SQLite-safe migration - no data loss, no table drops.
"""
import sqlite3
import os
from pathlib import Path


def get_database_path():
    """
    Find the database file in common locations.
    
    Returns:
        str: Path to database file or None if not found
    """
    # Common database locations
    candidates = [
        os.path.join("sas_management", "instance", "sas.db"),
        os.path.join("instance", "sas.db"),
        "sas.db",
        os.path.join(os.path.dirname(__file__), "..", "..", "sas_management", "instance", "sas.db"),
        os.path.join(os.path.dirname(__file__), "..", "..", "instance", "sas.db"),
    ]
    
    for candidate in candidates:
        abs_path = os.path.abspath(candidate)
        if os.path.exists(abs_path):
            return abs_path
    
    return None


def check_column_exists(cursor, table_name, column_name):
    """
    Check if a column exists in a table.
    
    Args:
        cursor: SQLite cursor
        table_name: Name of the table
        column_name: Name of the column
        
    Returns:
        bool: True if column exists, False otherwise
    """
    try:
        cursor.execute(f"PRAGMA table_info({table_name})")
        columns = [row[1] for row in cursor.fetchall()]
        return column_name in columns
    except Exception:
        return False


def fix_service_events_event_type_column(db_path=None):
    """
    Fix missing 'event_type' column in service_events table.
    
    Args:
        db_path: Optional database path. If None, will search for it.
    
    Returns:
        tuple: (success: bool, message: str)
    """
    if db_path is None:
        db_path = get_database_path()
    
    if not db_path:
        return False, "Database file not found"
    
    if not os.path.exists(db_path):
        return False, f"Database file does not exist: {db_path}"
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check if service_events table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='service_events'")
        if not cursor.fetchone():
            conn.close()
            return False, "service_events table does not exist"
        
        # Check if event_type column already exists
        if check_column_exists(cursor, "service_events", "event_type"):
            conn.close()
            return True, "[OK] service_events.event_type already exists"
        
        # Add event_type column - SQLite-safe
        try:
            cursor.execute("ALTER TABLE service_events ADD COLUMN event_type TEXT DEFAULT 'general'")
            conn.commit()
            conn.close()
            return True, "[FIX] service_events.event_type added"
        except sqlite3.OperationalError as e:
            error_msg = str(e).lower()
            if "duplicate column" in error_msg or "already exists" in error_msg:
                conn.close()
                return True, "[OK] service_events.event_type already exists (detected during add)"
            else:
                conn.rollback()
                conn.close()
                return False, f"Failed to add column: {e}"
        
    except Exception as e:
        try:
            conn.rollback()
            conn.close()
        except:
            pass
        return False, f"Error: {str(e)}"


if __name__ == "__main__":
    # Standalone execution
    success, message = fix_service_events_event_type_column()
    print(message)
    exit(0 if success else 1)

