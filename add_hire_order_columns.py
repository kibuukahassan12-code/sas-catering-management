"""Add missing columns to hire_order table using SQLAlchemy db.engine.execute()."""
import sqlite3
import os

# Database paths to check
db_paths = [
    os.path.join("instance", "sas.db"),
    os.path.join("instance", "site.db"),
]

def execute_alter_table(db_path):
    """Execute ALTER TABLE commands on the database."""
    if not os.path.exists(db_path):
        print(f"Database not found: {db_path}")
        return False
    
    print(f"\nProcessing database: {db_path}")
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # Check if table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='hire_order'")
        if not cursor.fetchone():
            print(f"  Table 'hire_order' does not exist in {db_path}")
            conn.close()
            return False
        
        # Execute ALTER TABLE commands
        commands = [
            ("ALTER TABLE hire_order ADD COLUMN client_name TEXT;", "client_name"),
            ("ALTER TABLE hire_order ADD COLUMN telephone TEXT;", "telephone"),
            ("ALTER TABLE hire_order ADD COLUMN deposit_amount REAL;", "deposit_amount"),
        ]
        
        for sql, col_name in commands:
            try:
                cursor.execute(sql)
                conn.commit()
                print(f"  [OK] Added column: {col_name}")
            except sqlite3.OperationalError as e:
                if "duplicate column" in str(e).lower():
                    print(f"  [SKIP] Column {col_name} already exists")
                else:
                    print(f"  [ERROR] Failed to add {col_name}: {e}")
                    conn.rollback()
        
        conn.close()
        return True
        
    except Exception as e:
        print(f"  [ERROR] Failed: {e}")
        conn.rollback()
        conn.close()
        return False

print("=" * 60)
print("Adding columns to hire_order table")
print("=" * 60)

for db_path in db_paths:
    execute_alter_table(db_path)

print("\n" + "=" * 60)
print("Migration completed!")
print("=" * 60)
