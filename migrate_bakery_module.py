"""Migration script to add bakery module tables and update BakeryItem model."""
import sqlite3
import os
from sqlalchemy.exc import OperationalError
from sqlalchemy import text

# Try to use Flask app context if available
try:
    from app import app, db
    USE_FLASK = True
except ImportError:
    USE_FLASK = False

def migrate_bakery():
    """Migrate bakery module tables and columns."""
    if USE_FLASK:
        with app.app_context():
            _migrate_with_flask()
    else:
        _migrate_with_sqlite()

def _migrate_with_flask():
    """Migrate using Flask app context."""
    print("Starting Bakery Department module migration (Flask)...")
    print("=" * 60)
    
    try:
        # Add new columns to bakery_item table
        new_columns = [
            ("selling_price", "NUMERIC(12,2) DEFAULT 0.00"),
            ("cost_price", "NUMERIC(12,2) DEFAULT 0.00"),
            ("preparation_time", "INTEGER"),
            ("created_at", "DATETIME"),
        ]
        
        for col_name, col_type in new_columns:
            try:
                db.session.execute(text(f"ALTER TABLE bakery_item ADD COLUMN {col_name} {col_type}"))
                db.session.commit()
                print(f"✓ Added column 'bakery_item.{col_name}'")
            except OperationalError as e:
                if "duplicate column name" in str(e).lower() or "already exists" in str(e).lower():
                    print(f"  Column 'bakery_item.{col_name}' already exists. Skipping.")
                else:
                    raise e
        
        # Create new bakery tables
        db.create_all()
        print("✓ Created all new bakery tables (bakery_order, bakery_order_item, bakery_production_task).")
        
        print("\n✅ Bakery Department migration completed successfully!")
        
    except Exception as e:
        print(f"\n❌ Migration error: {str(e)}")
        db.session.rollback()
        raise e

def _migrate_with_sqlite():
    """Migrate using direct SQLite connection."""
    # Get the database path
    db_path = os.path.join("instance", "site.db")
    if not os.path.exists(db_path):
        db_path = os.path.join("instance", "app.db")
    
    if not os.path.exists(db_path):
        print(f"Database not found at {db_path}.")
        print("Please run the app once to create the database, then run this migration.")
        return
    
    print(f"Connecting to database at {db_path}...")
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    print("Starting Bakery Department module migration (SQLite)...")
    
    # Add new columns to bakery_item table
    new_columns = [
        ("selling_price", "NUMERIC(12,2) DEFAULT 0.00"),
        ("cost_price", "NUMERIC(12,2) DEFAULT 0.00"),
        ("preparation_time", "INTEGER"),
        ("created_at", "DATETIME"),
    ]
    
    for col_name, col_type in new_columns:
        try:
            # Check if column exists
            cursor.execute("PRAGMA table_info(bakery_item)")
            columns = [row[1] for row in cursor.fetchall()]
            if col_name in columns:
                print(f"  Column 'bakery_item.{col_name}' already exists, skipping...")
            else:
                cursor.execute(f"ALTER TABLE bakery_item ADD COLUMN {col_name} {col_type}")
                conn.commit()
                print(f"[OK] Added column 'bakery_item.{col_name}'")
        except Exception as e:
            print(f"  Error adding 'bakery_item.{col_name}': {e}")
            conn.rollback()
    
    # Create bakery_order table
    try:
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS bakery_order (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                customer_id INTEGER,
                customer_name VARCHAR(255),
                customer_phone VARCHAR(50),
                customer_email VARCHAR(120),
                order_status VARCHAR(50) NOT NULL DEFAULT 'Draft',
                pickup_date DATE,
                delivery_address VARCHAR(500),
                bakery_notes TEXT,
                reference_image VARCHAR(500),
                final_image VARCHAR(500),
                total_amount NUMERIC(12,2) NOT NULL DEFAULT 0.00,
                created_at DATETIME NOT NULL,
                updated_at DATETIME NOT NULL,
                created_by INTEGER,
                FOREIGN KEY (customer_id) REFERENCES client(id),
                FOREIGN KEY (created_by) REFERENCES user(id)
            )
        """)
        conn.commit()
        print("[OK] Created table 'bakery_order'")
    except Exception as e:
        print(f"  Error creating 'bakery_order' table: {e}")
        conn.rollback()
    
    # Create bakery_order_item table
    try:
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS bakery_order_item (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                order_id INTEGER NOT NULL,
                item_id INTEGER,
                item_name VARCHAR(255) NOT NULL,
                qty INTEGER NOT NULL DEFAULT 1,
                custom_price NUMERIC(12,2),
                custom_notes TEXT,
                created_at DATETIME NOT NULL,
                FOREIGN KEY (order_id) REFERENCES bakery_order(id),
                FOREIGN KEY (item_id) REFERENCES bakery_item(id)
            )
        """)
        conn.commit()
        print("[OK] Created table 'bakery_order_item'")
    except Exception as e:
        print(f"  Error creating 'bakery_order_item' table: {e}")
        conn.rollback()
    
    # Create bakery_production_task table
    try:
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS bakery_production_task (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                order_id INTEGER NOT NULL,
                staff_id INTEGER NOT NULL,
                task_type VARCHAR(100) NOT NULL,
                start_time DATETIME,
                end_time DATETIME,
                status VARCHAR(50) NOT NULL DEFAULT 'Pending',
                notes TEXT,
                created_at DATETIME NOT NULL,
                FOREIGN KEY (order_id) REFERENCES bakery_order(id),
                FOREIGN KEY (staff_id) REFERENCES user(id)
            )
        """)
        conn.commit()
        print("[OK] Created table 'bakery_production_task'")
    except Exception as e:
        print(f"  Error creating 'bakery_production_task' table: {e}")
        conn.rollback()
    
    conn.close()
    print("\n✅ Bakery Department migration completed successfully!")

if __name__ == "__main__":
    migrate_bakery()

