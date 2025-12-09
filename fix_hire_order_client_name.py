"""Migration script to add client_name and telephone columns to hire_order table."""
import sqlite3
import os

# Check both possible database paths
db_paths = [
    os.path.join("instance", "sas.db"),  # Primary database
    os.path.join("instance", "site.db"),  # Alternative database
]

def migrate_database(db_path):
    """Add missing columns to hire_order table."""
    if not os.path.exists(db_path):
        print(f"  Database not found at {db_path}, skipping...")
        return False
    
    print(f"\nConnecting to database at {db_path}...")
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # Check if hire_order table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='hire_order'")
        if not cursor.fetchone():
            print(f"  Table 'hire_order' does not exist in {db_path}, skipping...")
            conn.close()
            return False
        
        # Get existing columns
        cursor.execute("PRAGMA table_info(hire_order)")
        existing_columns = [row[1] for row in cursor.fetchall()]
        print(f"  Existing columns: {', '.join(existing_columns)}")
        
        # Columns to add
        columns_to_add = [
            ("client_name", "TEXT"),
            ("telephone", "TEXT"),
        ]
        
        added_any = False
        for col_name, col_type in columns_to_add:
            if col_name in existing_columns:
                print(f"  Column 'hire_order.{col_name}' already exists, skipping...")
            else:
                try:
                    cursor.execute(f"ALTER TABLE hire_order ADD COLUMN {col_name} {col_type}")
                    conn.commit()
                    print(f"  [OK] Added column 'hire_order.{col_name}'")
                    added_any = True
                except Exception as e:
                    print(f"  [ERROR] Failed to add 'hire_order.{col_name}': {e}")
                    conn.rollback()
        
        conn.close()
        return added_any
        
    except Exception as e:
        print(f"  [ERROR] Migration failed for {db_path}: {e}")
        conn.rollback()
        conn.close()
        return False

print("=" * 60)
print("Hire Order Client Name Migration")
print("=" * 60)

migrated = False
for db_path in db_paths:
    if migrate_database(db_path):
        migrated = True

if migrated:
    print("\n" + "=" * 60)
    print("Migration completed successfully!")
    print("The client_name and telephone columns have been added.")
    print("Please restart your Flask server for changes to take effect.")
    print("=" * 60)
else:
    print("\n" + "=" * 60)
    print("No migrations were needed or databases were not found.")
    print("=" * 60)

