"""Migration script to add new fields to InventoryItem and HireOrder models."""
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

print("Starting Hire module enhancements migration...")

# Add new columns to inventory_item table
new_inventory_columns = [
    ("category", "VARCHAR(100)"),
    ("sku", "VARCHAR(100)"),
    ("replacement_cost", "NUMERIC(10,2)"),
    ("condition", "VARCHAR(50) DEFAULT 'Good'"),
    ("location", "VARCHAR(100)"),
    ("tags", "VARCHAR(255)"),
    ("created_at", "DATETIME"),
    ("updated_at", "DATETIME"),
]

for col_name, col_type in new_inventory_columns:
    try:
        # Check if column exists
        cursor.execute(f"PRAGMA table_info(inventory_item)")
        columns = [row[1] for row in cursor.fetchall()]
        if col_name in columns:
            print(f"  Column 'inventory_item.{col_name}' already exists, skipping...")
        else:
            cursor.execute(f"ALTER TABLE inventory_item ADD COLUMN {col_name} {col_type}")
            conn.commit()
            print(f"[OK] Added column 'inventory_item.{col_name}'")
    except Exception as e:
        print(f"  Error adding 'inventory_item.{col_name}': {e}")
        conn.rollback()

# Add new columns to hire_order table
new_hire_order_columns = [
    ("reference", "VARCHAR(120)"),
    ("status", "VARCHAR(50) DEFAULT 'Draft'"),
    ("delivery_date", "DATE"),
    ("pickup_date", "DATE"),
    ("deposit_amount", "NUMERIC(12,2)"),
    ("created_at", "DATETIME"),
    ("updated_at", "DATETIME"),
]

for col_name, col_type in new_hire_order_columns:
    try:
        # Check if column exists
        cursor.execute(f"PRAGMA table_info(hire_order)")
        columns = [row[1] for row in cursor.fetchall()]
        if col_name in columns:
            print(f"  Column 'hire_order.{col_name}' already exists, skipping...")
        else:
            cursor.execute(f"ALTER TABLE hire_order ADD COLUMN {col_name} {col_type}")
            conn.commit()
            print(f"[OK] Added column 'hire_order.{col_name}'")
    except Exception as e:
        print(f"  Error adding 'hire_order.{col_name}': {e}")
        conn.rollback()

# Add new columns to hire_order_item table
new_order_item_columns = [
    ("unit_price", "NUMERIC(10,2) DEFAULT 0.00"),
    ("subtotal", "NUMERIC(12,2) DEFAULT 0.00"),
    ("returned_quantity", "INTEGER DEFAULT 0"),
    ("damaged_quantity", "INTEGER DEFAULT 0"),
]

for col_name, col_type in new_order_item_columns:
    try:
        # Check if column exists
        cursor.execute(f"PRAGMA table_info(hire_order_item)")
        columns = [row[1] for row in cursor.fetchall()]
        if col_name in columns:
            print(f"  Column 'hire_order_item.{col_name}' already exists, skipping...")
        else:
            cursor.execute(f"ALTER TABLE hire_order_item ADD COLUMN {col_name} {col_type}")
            conn.commit()
            print(f"[OK] Added column 'hire_order_item.{col_name}'")
    except Exception as e:
        print(f"  Error adding 'hire_order_item.{col_name}': {e}")
        conn.rollback()

# Update existing records to set default values
try:
    cursor.execute("UPDATE inventory_item SET condition = 'Good' WHERE condition IS NULL")
    cursor.execute("UPDATE hire_order SET status = 'Draft' WHERE status IS NULL")
    cursor.execute("UPDATE hire_order_item SET unit_price = 0.00 WHERE unit_price IS NULL")
    cursor.execute("UPDATE hire_order_item SET subtotal = 0.00 WHERE subtotal IS NULL")
    cursor.execute("UPDATE hire_order_item SET returned_quantity = 0 WHERE returned_quantity IS NULL")
    cursor.execute("UPDATE hire_order_item SET damaged_quantity = 0 WHERE damaged_quantity IS NULL")
    conn.commit()
    print("[OK] Updated existing records with default values")
except Exception as e:
    print(f"  Note: {e}")
    conn.rollback()

conn.close()
print("\nMigration completed! Hire module enhancements are now available.")
print("You may need to restart the application for changes to take full effect.")
