"""Migration script to add POS System tables."""
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

print("Starting POS System module migration...")

# Create pos_device table
try:
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS pos_device (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name VARCHAR(120) NOT NULL,
            terminal_code VARCHAR(64) UNIQUE NOT NULL,
            location VARCHAR(255),
            is_active BOOLEAN DEFAULT 1,
            last_seen DATETIME,
            created_at DATETIME
        )
    """)
    conn.commit()
    print("[OK] Created table 'pos_device'")
except Exception as e:
    print(f"  Error creating 'pos_device' table: {e}")
    conn.rollback()

# Create pos_shift table
try:
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS pos_shift (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            device_id INTEGER,
            user_id INTEGER NOT NULL,
            started_at DATETIME NOT NULL,
            ended_at DATETIME,
            starting_cash NUMERIC(12,2) DEFAULT 0.0,
            ending_cash NUMERIC(12,2),
            status VARCHAR(50) DEFAULT 'open',
            FOREIGN KEY (device_id) REFERENCES pos_device(id),
            FOREIGN KEY (user_id) REFERENCES user(id)
        )
    """)
    conn.commit()
    print("[OK] Created table 'pos_shift'")
except Exception as e:
    print(f"  Error creating 'pos_shift' table: {e}")
    conn.rollback()

# Create pos_order table
try:
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS pos_order (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            reference VARCHAR(120) UNIQUE NOT NULL,
            shift_id INTEGER,
            device_id INTEGER,
            client_id INTEGER,
            order_time DATETIME NOT NULL,
            total_amount NUMERIC(14,2) DEFAULT 0.0,
            tax_amount NUMERIC(14,2) DEFAULT 0.0,
            discount_amount NUMERIC(14,2) DEFAULT 0.0,
            status VARCHAR(50) DEFAULT 'draft',
            is_delivery BOOLEAN DEFAULT 0,
            delivery_date DATETIME,
            delivery_address VARCHAR(255),
            delivery_driver_id INTEGER,
            created_at DATETIME,
            updated_at DATETIME,
            FOREIGN KEY (shift_id) REFERENCES pos_shift(id),
            FOREIGN KEY (device_id) REFERENCES pos_device(id),
            FOREIGN KEY (client_id) REFERENCES client(id),
            FOREIGN KEY (delivery_driver_id) REFERENCES user(id)
        )
    """)
    conn.commit()
    print("[OK] Created table 'pos_order'")
except Exception as e:
    print(f"  Error creating 'pos_order' table: {e}")
    conn.rollback()

# Create pos_order_line table
try:
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS pos_order_line (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            order_id INTEGER NOT NULL,
            product_id INTEGER,
            product_name VARCHAR(255) NOT NULL,
            qty INTEGER DEFAULT 1,
            unit_price NUMERIC(12,2) DEFAULT 0.0,
            line_total NUMERIC(14,2) DEFAULT 0.0,
            note VARCHAR(255),
            is_kitchen_item BOOLEAN DEFAULT 1,
            FOREIGN KEY (order_id) REFERENCES pos_order(id)
        )
    """)
    conn.commit()
    print("[OK] Created table 'pos_order_line'")
except Exception as e:
    print(f"  Error creating 'pos_order_line' table: {e}")
    conn.rollback()

# Create pos_payment table
try:
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS pos_payment (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            order_id INTEGER NOT NULL,
            amount NUMERIC(14,2) DEFAULT 0.0,
            method VARCHAR(50) NOT NULL,
            ref VARCHAR(120),
            payment_time DATETIME NOT NULL,
            created_at DATETIME,
            FOREIGN KEY (order_id) REFERENCES pos_order(id)
        )
    """)
    conn.commit()
    print("[OK] Created table 'pos_payment'")
except Exception as e:
    print(f"  Error creating 'pos_payment' table: {e}")
    conn.rollback()

# Create pos_receipt table
try:
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS pos_receipt (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            payment_id INTEGER NOT NULL,
            receipt_ref VARCHAR(120) UNIQUE NOT NULL,
            pdf_path VARCHAR(255),
            issued_at DATETIME NOT NULL,
            FOREIGN KEY (payment_id) REFERENCES pos_payment(id)
        )
    """)
    conn.commit()
    print("[OK] Created table 'pos_receipt'")
except Exception as e:
    print(f"  Error creating 'pos_receipt' table: {e}")
    conn.rollback()

# Check if tables already exist
try:
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name LIKE 'pos_%'")
    existing_tables = [row[0] for row in cursor.fetchall()]
    if existing_tables:
        print(f"  Note: POS tables already exist: {', '.join(existing_tables)}")
except Exception as e:
    print(f"  Note: {e}")

conn.close()
print("\nMigration completed! POS System module tables are now available.")
print("You may need to restart the application for changes to take full effect.")

