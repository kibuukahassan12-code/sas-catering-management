"""Migration script to add missing fields to pos_product table."""
import sqlite3
import os
import sys

# Get the database path
db_path = os.path.join("sas_management", "instance", "sas.db")
if not os.path.exists(db_path):
    db_path = os.path.join("instance", "sas.db")
if not os.path.exists(db_path):
    db_path = os.path.join("sas_management", "instance", "app.db")
if not os.path.exists(db_path):
    print(f"Database not found. Please ensure the database exists.")
    sys.exit(1)

print(f"Connecting to database at {db_path}...")
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

print("Adding missing columns to pos_product table...")

# List of columns to add (if they don't exist)
columns_to_add = [
    ("description", "TEXT"),
    ("image_url", "VARCHAR(500)"),
    ("barcode", "VARCHAR(100)"),
    ("sku", "VARCHAR(100)"),
    ("tax_rate", "NUMERIC(5,2) DEFAULT 18.00"),
    ("is_active", "BOOLEAN DEFAULT 1"),
    ("created_by", "INTEGER"),
]

for column_name, column_type in columns_to_add:
    try:
        # Check if column exists
        cursor.execute(f"PRAGMA table_info(pos_product)")
        existing_columns = [row[1] for row in cursor.fetchall()]
        
        if column_name not in existing_columns:
            cursor.execute(f"ALTER TABLE pos_product ADD COLUMN {column_name} {column_type}")
            conn.commit()
            print(f"  [OK] Added column '{column_name}'")
        else:
            print(f"  [SKIP] Column '{column_name}' already exists")
    except sqlite3.OperationalError as e:
        error_msg = str(e).lower()
        if "duplicate column" in error_msg or "already exists" in error_msg:
            print(f"  [SKIP] Column '{column_name}' already exists")
        else:
            print(f"  [ERROR] Could not add column '{column_name}': {e}")
            conn.rollback()

# Update is_active to match is_available for existing records
try:
    cursor.execute("UPDATE pos_product SET is_active = is_available WHERE is_active IS NULL")
    conn.commit()
    print("  [OK] Updated is_active values from is_available")
except Exception as e:
    print(f"  [WARN] Could not update is_active: {e}")

conn.close()
print("\nMigration complete!")
print("POS products can now be saved and sold with all required fields.")

