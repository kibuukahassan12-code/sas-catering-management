"""Migration script to add Production Department tables."""
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

print("Starting Production Department module migration...")

# Create recipe table
try:
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS recipe (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name VARCHAR(255) NOT NULL,
            description TEXT,
            portions INTEGER DEFAULT 1,
            ingredients TEXT NOT NULL,
            prep_time_mins INTEGER DEFAULT 0,
            cook_time_mins INTEGER DEFAULT 0,
            cost_per_portion NUMERIC(12,2) DEFAULT 0.0,
            created_at DATETIME
        )
    """)
    conn.commit()
    print("[OK] Created table 'recipe'")
except Exception as e:
    print(f"  Error creating 'recipe' table: {e}")
    conn.rollback()

# Create production_order table
try:
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS production_order (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            event_id INTEGER,
            reference VARCHAR(120) UNIQUE NOT NULL,
            scheduled_prep DATETIME NOT NULL,
            scheduled_cook DATETIME,
            scheduled_pack DATETIME,
            scheduled_load DATETIME,
            total_portions INTEGER DEFAULT 0,
            total_cost NUMERIC(12,2) DEFAULT 0.0,
            status VARCHAR(50) DEFAULT 'Planned',
            assigned_team VARCHAR(255),
            notes TEXT,
            created_at DATETIME,
            updated_at DATETIME,
            FOREIGN KEY (event_id) REFERENCES event(id)
        )
    """)
    conn.commit()
    print("[OK] Created table 'production_order'")
except Exception as e:
    print(f"  Error creating 'production_order' table: {e}")
    conn.rollback()

# Create production_line_item table
try:
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS production_line_item (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            order_id INTEGER NOT NULL,
            recipe_id INTEGER NOT NULL,
            recipe_name VARCHAR(255) NOT NULL,
            portions INTEGER DEFAULT 0,
            unit VARCHAR(50) DEFAULT 'portion',
            status VARCHAR(50) DEFAULT 'Pending',
            created_at DATETIME,
            FOREIGN KEY (order_id) REFERENCES production_order(id),
            FOREIGN KEY (recipe_id) REFERENCES recipe(id)
        )
    """)
    conn.commit()
    print("[OK] Created table 'production_line_item'")
except Exception as e:
    print(f"  Error creating 'production_line_item' table: {e}")
    conn.rollback()

# Check if tables already exist and skip if they do
try:
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name IN ('recipe', 'production_order', 'production_line_item')")
    existing_tables = [row[0] for row in cursor.fetchall()]
    if existing_tables:
        print(f"  Note: Tables already exist: {', '.join(existing_tables)}")
except Exception as e:
    print(f"  Note: {e}")

conn.close()
print("\nMigration completed! Production Department module tables are now available.")
print("You may need to restart the application for changes to take full effect.")

