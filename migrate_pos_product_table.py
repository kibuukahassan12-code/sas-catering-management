"""Migration script to create POS Product table."""
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

print("Creating pos_product table...")

try:
    # Create pos_product table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS pos_product (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name VARCHAR(200) NOT NULL,
            description TEXT,
            category VARCHAR(100),
            price NUMERIC(12, 2) NOT NULL DEFAULT 0.0,
            image_url VARCHAR(500),
            is_active BOOLEAN NOT NULL DEFAULT 1,
            barcode VARCHAR(100) UNIQUE,
            sku VARCHAR(100) UNIQUE,
            tax_rate NUMERIC(5, 2) NOT NULL DEFAULT 18.0,
            created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
            created_by INTEGER,
            FOREIGN KEY(created_by) REFERENCES user(id)
        )
    """)
    print("[OK] Created 'pos_product' table")
    
    # Create index on is_active for faster queries
    try:
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_pos_product_is_active ON pos_product(is_active)")
        print("[OK] Created index on 'is_active'")
    except Exception as e:
        print(f"[SKIP] Index creation: {e}")
    
    # Create unique indexes
    try:
        cursor.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_pos_product_barcode ON pos_product(barcode) WHERE barcode IS NOT NULL")
        print("[OK] Created unique index on 'barcode'")
    except Exception as e:
        print(f"[SKIP] Index creation: {e}")
    
    try:
        cursor.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_pos_product_sku ON pos_product(sku) WHERE sku IS NOT NULL")
        print("[OK] Created unique index on 'sku'")
    except Exception as e:
        print(f"[SKIP] Index creation: {e}")
    
    conn.commit()
    print("\nPOS Product migration completed successfully!")
    
except Exception as e:
    print(f"\n[ERROR] Migration failed: {e}")
    conn.rollback()
    exit(1)
finally:
    conn.close()

