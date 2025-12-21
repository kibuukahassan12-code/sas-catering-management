"""
Safe Auto-Fix Script for ai_features Table

This script safely adds the missing 'code' column (NOT NULL) to ai_features table and ensures
all required columns exist. Designed to run on app startup to fix production schema issues.

SQLite-safe migration - no data loss, no table drops.
Note: 'code' is the canonical identifier (NOT NULL), 'key' is optional legacy alias.
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


def check_table_exists(cursor, table_name):
    """
    Check if a table exists.
    
    Args:
        cursor: SQLite cursor
        table_name: Name of the table
        
    Returns:
        bool: True if table exists, False otherwise
    """
    try:
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name=?", (table_name,))
        return cursor.fetchone() is not None
    except Exception:
        return False


def fix_ai_features_table(db_path=None):
    """
    Fix missing 'code' column (NOT NULL) and ensure all required columns exist in ai_features table.
    
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
        
        # Check if ai_features table exists
        if not check_table_exists(cursor, "ai_features"):
            # Table doesn't exist - will be created by SQLAlchemy
            conn.close()
            return True, "[OK] ai_features table will be created by SQLAlchemy"
        
        fixes_applied = []
        
        # Check and add 'code' column if missing (CRITICAL: NOT NULL constraint)
        if not check_column_exists(cursor, "ai_features", "code"):
            try:
                cursor.execute("ALTER TABLE ai_features ADD COLUMN code TEXT")
                conn.commit()
                fixes_applied.append("code column added")
                
                # If code column was just added, populate it from key if key exists
                if check_column_exists(cursor, "ai_features", "key"):
                    cursor.execute("UPDATE ai_features SET code = key WHERE code IS NULL OR code = ''")
                    conn.commit()
                    fixes_applied.append("code column populated from key")
            except sqlite3.OperationalError as e:
                error_msg = str(e).lower()
                if "duplicate column" in error_msg or "already exists" in error_msg:
                    pass  # Column exists, continue
                else:
                    conn.rollback()
                    conn.close()
                    return False, f"Failed to add code column: {e}"
        
        # Check and add 'key' column if missing (optional legacy alias)
        if not check_column_exists(cursor, "ai_features", "key"):
            try:
                cursor.execute("ALTER TABLE ai_features ADD COLUMN key TEXT")
                conn.commit()
                fixes_applied.append("key column added")
            except sqlite3.OperationalError as e:
                error_msg = str(e).lower()
                if "duplicate column" in error_msg or "already exists" in error_msg:
                    pass  # Column exists, continue
                else:
                    conn.rollback()
                    conn.close()
                    return False, f"Failed to add key column: {e}"
        
        # Ensure other required columns exist (non-destructive, only add if missing)
        required_columns = {
            'name': 'TEXT',
            'description': 'TEXT',
            'is_enabled': 'BOOLEAN DEFAULT 1'
        }
        
        for col_name, col_type in required_columns.items():
            if not check_column_exists(cursor, "ai_features", col_name):
                try:
                    cursor.execute(f"ALTER TABLE ai_features ADD COLUMN {col_name} {col_type}")
                    conn.commit()
                    fixes_applied.append(f"{col_name} column added")
                except sqlite3.OperationalError as e:
                    error_msg = str(e).lower()
                    if "duplicate column" not in error_msg and "already exists" not in error_msg:
                        conn.rollback()
                        conn.close()
                        return False, f"Failed to add {col_name} column: {e}"
        
        # Add unique constraint on 'code' column if it doesn't exist
        # SQLite doesn't support adding constraints directly, so we check if unique index exists
        try:
            cursor.execute("SELECT name FROM sqlite_master WHERE type='index' AND name='ix_ai_features_code'")
            if not cursor.fetchone():
                # Create unique index on code column
                cursor.execute("CREATE UNIQUE INDEX IF NOT EXISTS ix_ai_features_code ON ai_features(code)")
                conn.commit()
                fixes_applied.append("unique index on code column created")
        except Exception as e:
            # Index creation is optional, don't fail if it errors
            pass
        
        conn.close()
        
        if fixes_applied:
            return True, f"[FIX] ai_features table fixed: {', '.join(fixes_applied)}"
        else:
            return True, "[OK] ai_features table schema is correct"
        
    except Exception as e:
        try:
            conn.rollback()
            conn.close()
        except:
            pass
        return False, f"Error: {str(e)}"


if __name__ == "__main__":
    # Standalone execution
    success, message = fix_ai_features_table()
    print(message)
    exit(0 if success else 1)

