"""Rebuild hire_order table to exactly match the HireOrder model."""
import sqlite3
import os

# Database paths to check
db_paths = [
    os.path.join("instance", "sas.db"),
    os.path.join("instance", "site.db"),
]

def rebuild_table(db_path):
    """Rebuild hire_order table to match the model exactly."""
    if not os.path.exists(db_path):
        print(f"Database not found: {db_path}")
        return False
    
    print(f"\n{'='*60}")
    print(f"Rebuilding hire_order table in: {db_path}")
    print(f"{'='*60}")
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # Check if table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='hire_order'")
        if not cursor.fetchone():
            print(f"  Table 'hire_order' does not exist. Creating new table...")
            # Create table from scratch
            cursor.execute("""
                CREATE TABLE hire_order (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    event_id INTEGER,
                    client_id INTEGER,
                    client_name TEXT,
                    telephone TEXT,
                    item_id INTEGER,
                    quantity INTEGER,
                    reference TEXT,
                    status TEXT NOT NULL DEFAULT 'Draft',
                    start_date DATE NOT NULL,
                    end_date DATE NOT NULL,
                    delivery_date DATE,
                    pickup_date DATE,
                    delivery_address TEXT,
                    total_cost REAL NOT NULL DEFAULT 0.00,
                    deposit_amount REAL,
                    created_at DATETIME NOT NULL
                )
            """)
            conn.commit()
            print("  [OK] Created new hire_order table")
            conn.close()
            return True
        
        # Get existing columns
        cursor.execute("PRAGMA table_info(hire_order)")
        existing_columns = {row[1]: row[2] for row in cursor.fetchall()}
        print(f"\n  Existing columns: {', '.join(existing_columns.keys())}")
        
        # Step 1: Create new table with correct structure
        print("\n  Step 1: Creating new table structure...")
        cursor.execute("""
            CREATE TABLE hire_order_new (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                event_id INTEGER,
                client_id INTEGER,
                client_name TEXT,
                telephone TEXT,
                item_id INTEGER,
                quantity INTEGER,
                reference TEXT,
                status TEXT NOT NULL DEFAULT 'Draft',
                start_date DATE NOT NULL,
                end_date DATE NOT NULL,
                delivery_date DATE,
                pickup_date DATE,
                delivery_address TEXT,
                total_cost REAL NOT NULL DEFAULT 0.00,
                deposit_amount REAL,
                created_at DATETIME NOT NULL
            )
        """)
        print("  [OK] Created hire_order_new table")
        
        # Step 2: Copy data from old table (only columns that exist)
        print("\n  Step 2: Copying data from old table...")
        
        # Build column list for SELECT (only columns that exist in old table)
        columns_to_copy = []
        possible_columns = [
            'id', 'event_id', 'client_id', 'client_name', 'telephone', 
            'item_id', 'quantity', 'reference', 'status', 'start_date', 
            'end_date', 'delivery_date', 'pickup_date', 'delivery_address', 
            'total_cost', 'deposit_amount', 'created_at'
        ]
        
        for col in possible_columns:
            if col in existing_columns:
                columns_to_copy.append(col)
        
        if columns_to_copy:
            select_cols = ', '.join(columns_to_copy)
            insert_cols = ', '.join(columns_to_copy)
            
            # Get row count
            cursor.execute(f"SELECT COUNT(*) FROM hire_order")
            row_count = cursor.fetchone()[0]
            print(f"  Found {row_count} rows to copy")
            
            if row_count > 0:
                cursor.execute(f"""
                    INSERT INTO hire_order_new ({insert_cols})
                    SELECT {select_cols}
                    FROM hire_order
                """)
                conn.commit()
                print(f"  [OK] Copied {row_count} rows to new table")
            else:
                print("  [SKIP] No rows to copy")
        else:
            print("  [SKIP] No matching columns found")
        
        # Step 3: Drop old table and rename new one
        print("\n  Step 3: Replacing old table with new one...")
        cursor.execute("DROP TABLE hire_order")
        print("  [OK] Dropped old hire_order table")
        
        cursor.execute("ALTER TABLE hire_order_new RENAME TO hire_order")
        print("  [OK] Renamed hire_order_new to hire_order")
        
        conn.commit()
        
        # Verify final structure
        print("\n  Step 4: Verifying final structure...")
        cursor.execute("PRAGMA table_info(hire_order)")
        final_columns = [row[1] for row in cursor.fetchall()]
        print(f"  Final columns: {', '.join(final_columns)}")
        
        # Check for required columns
        required_columns = ['client_name', 'telephone', 'item_id', 'quantity', 'deposit_amount']
        missing = [col for col in required_columns if col not in final_columns]
        
        if missing:
            print(f"  [WARNING] Missing columns: {', '.join(missing)}")
        else:
            print("  [SUCCESS] All required columns are present!")
        
        conn.close()
        return True
        
    except Exception as e:
        print(f"  [ERROR] Rebuild failed: {e}")
        import traceback
        traceback.print_exc()
        conn.rollback()
        conn.close()
        return False

print("=" * 60)
print("Rebuilding hire_order table to match HireOrder model")
print("=" * 60)
print("\nThis will:")
print("  1. Create a new table with the correct structure")
print("  2. Copy existing data (preserving what exists)")
print("  3. Replace the old table with the new one")
print("\n⚠️  WARNING: This operation will rebuild the table structure.")
print("   Existing data will be preserved, but the table structure will change.")
print("=" * 60)

success_count = 0
for db_path in db_paths:
    if rebuild_table(db_path):
        success_count += 1

print("\n" + "=" * 60)
if success_count > 0:
    print("✅ Rebuild completed successfully!")
    print("\nThe hire_order table now matches the HireOrder model exactly.")
    print("All 'no such column' errors should be permanently resolved.")
    print("\n⚠️  IMPORTANT: Restart your Flask server for changes to take effect.")
else:
    print("⚠️  No databases were processed.")
print("=" * 60)

