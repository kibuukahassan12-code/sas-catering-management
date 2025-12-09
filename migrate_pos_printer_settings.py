"""Migration script to add printer settings to POS Device table."""
import sqlite3
import os

# Get the database path
db_path = os.path.join("instance", "site.db")
if not os.path.exists(db_path):
    print(f"Database not found at {db_path}. Creating new database structure...")
    print("Please run the app once to create the database, then run this migration.")
    exit(1)

print(f"Connecting to database at {db_path}...")
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

print("Adding printer settings columns to pos_device table...")

# Add printer settings columns if they don't exist
columns_to_add = [
    ("printer_enabled", "BOOLEAN DEFAULT 0"),
    ("auto_print_receipts", "BOOLEAN DEFAULT 0"),
    ("printer_name", "VARCHAR(255)"),
    ("printer_paper_width", "INTEGER DEFAULT 80"),
    ("printer_copies", "INTEGER DEFAULT 1"),
]

for column_name, column_type in columns_to_add:
    try:
        # Check if column already exists
        cursor.execute(f"PRAGMA table_info(pos_device)")
        columns = [col[1] for col in cursor.fetchall()]
        
        if column_name not in columns:
            cursor.execute(f"ALTER TABLE pos_device ADD COLUMN {column_name} {column_type}")
            print(f"[OK] Added column '{column_name}' to 'pos_device' table")
        else:
            print(f"[SKIP] Column '{column_name}' already exists")
    except Exception as e:
        print(f"  Error adding column '{column_name}': {e}")
        conn.rollback()

conn.commit()
print("\nPrinter settings migration completed successfully!")
conn.close()

