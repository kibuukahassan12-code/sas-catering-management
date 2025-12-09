"""Comprehensive migration script to fix hire_order table schema permanently."""
import sqlite3
import os

# Check both possible database paths
db_paths = [
    os.path.join("instance", "sas.db"),  # Primary database
    os.path.join("instance", "site.db"),  # Alternative database
]

def get_existing_columns(cursor, table_name):
    """Get list of existing column names for a table."""
    cursor.execute(f"PRAGMA table_info({table_name})")
    return [row[1] for row in cursor.fetchall()]

def add_column_if_missing(cursor, conn, table_name, col_name, col_type, default_value=None):
    """Add a column to a table if it doesn't exist."""
    existing_columns = get_existing_columns(cursor, table_name)
    
    if col_name in existing_columns:
        print(f"  ✓ Column '{table_name}.{col_name}' already exists")
        return False
    
    try:
        sql = f"ALTER TABLE {table_name} ADD COLUMN {col_name} {col_type}"
        if default_value:
            sql += f" DEFAULT {default_value}"
        cursor.execute(sql)
        conn.commit()
        print(f"  [OK] Added column '{table_name}.{col_name}' ({col_type})")
        return True
    except Exception as e:
        print(f"  [ERROR] Failed to add '{table_name}.{col_name}': {e}")
        conn.rollback()
        return False

def migrate_database(db_path):
    """Add all missing columns to hire_order table."""
    if not os.path.exists(db_path):
        print(f"  Database not found at {db_path}, skipping...")
        return False
    
    print(f"\n{'='*60}")
    print(f"Migrating database: {db_path}")
    print(f"{'='*60}")
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # Check if hire_order table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='hire_order'")
        if not cursor.fetchone():
            print(f"  Table 'hire_order' does not exist, skipping...")
            conn.close()
            return False
        
        # Get existing columns
        existing_columns = get_existing_columns(cursor, "hire_order")
        print(f"\n  Existing columns in hire_order: {', '.join(existing_columns)}")
        
        # Define all required columns based on the model
        required_columns = [
            ("client_name", "TEXT", None),
            ("telephone", "TEXT", None),
            ("deposit_amount", "REAL", None),
            ("item_id", "INTEGER", None),
            ("quantity", "INTEGER", None),
            ("status", "TEXT", "'Draft'"),
            ("start_date", "DATE", None),
            ("end_date", "DATE", None),
            ("created_at", "DATETIME", None),
        ]
        
        print(f"\n  Checking and adding missing columns...")
        added_any = False
        for col_name, col_type, default_value in required_columns:
            if add_column_if_missing(cursor, conn, "hire_order", col_name, col_type, default_value):
                added_any = True
        
        # Verify all columns now exist
        print(f"\n  Verifying final schema...")
        final_columns = get_existing_columns(cursor, "hire_order")
        print(f"  Final columns: {', '.join(final_columns)}")
        
        # Check for critical columns
        critical_columns = ["client_name", "telephone", "deposit_amount"]
        missing_critical = [col for col in critical_columns if col not in final_columns]
        
        if missing_critical:
            print(f"\n  [WARNING] Critical columns still missing: {', '.join(missing_critical)}")
        else:
            print(f"\n  [SUCCESS] All critical columns are present!")
        
        conn.close()
        return added_any
        
    except Exception as e:
        print(f"  [ERROR] Migration failed: {e}")
        import traceback
        traceback.print_exc()
        conn.rollback()
        conn.close()
        return False

print("=" * 60)
print("Hire Order Schema Fix - Permanent Migration")
print("=" * 60)
print("\nThis script will ensure all required columns exist in hire_order table.")
print("It will add any missing columns without affecting existing data.\n")

migrated = False
for db_path in db_paths:
    if migrate_database(db_path):
        migrated = True

print("\n" + "=" * 60)
if migrated:
    print("Migration completed successfully!")
    print("\nThe following columns have been verified/added:")
    print("  - client_name (TEXT)")
    print("  - telephone (TEXT)")
    print("  - deposit_amount (REAL)")
    print("  - item_id (INTEGER)")
    print("  - quantity (INTEGER)")
    print("  - status (TEXT)")
    print("  - start_date (DATE)")
    print("  - end_date (DATE)")
    print("  - created_at (DATETIME)")
    print("\n✅ The error 'no such column: hire_order.client_name' should now be resolved.")
else:
    print("No migrations were needed - all columns already exist.")
print("\n⚠️  IMPORTANT: Restart your Flask server for changes to take effect.")
print("=" * 60)

