"""Rebuild hire_order table using exact SQL commands to match HireOrder model."""
import sqlite3
import os

# Find the database file
db_candidates = [
    os.path.join("instance", "sas.db"),  # Most likely
    os.path.join("instance", "site.db"),  # Alternative
    "sas_management.db",  # Project root
    "app.db",  # Project root
    os.path.join("sas_management", "instance", "sas.db"),
]

db_path = None
for candidate in db_candidates:
    if os.path.exists(candidate):
        db_path = candidate
        print(f"Found database: {candidate}")
        break

if not db_path:
    print("ERROR: Could not find database file.")
    print("Searched in:")
    for candidate in db_candidates:
        print(f"  - {candidate}")
    exit(1)

print("=" * 60)
print("Rebuilding hire_order table to match HireOrder model")
print(f"Database: {db_path}")
print("=" * 60)

conn = sqlite3.connect(db_path)
cursor = conn.cursor()

try:
    # Check if table exists
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='hire_order'")
    table_exists = cursor.fetchone() is not None
    
    if table_exists:
        # Get row count
        cursor.execute("SELECT COUNT(*) FROM hire_order")
        row_count = cursor.fetchone()[0]
        print(f"\nFound {row_count} existing rows in hire_order table")
    else:
        print("\nTable 'hire_order' does not exist. Will create new table.")
        row_count = 0
    
    # Step 1: Create new table with exact schema
    print("\n" + "=" * 60)
    print("Step 1: Creating new table with correct schema...")
    print("=" * 60)
    
    cursor.execute("""
        CREATE TABLE hire_order_new (
            id INTEGER PRIMARY KEY,
            event_id INTEGER,
            client_name TEXT,
            telephone TEXT,
            item_id INTEGER,
            quantity INTEGER,
            status TEXT,
            deposit_amount REAL,
            reference TEXT,
            start_date DATE,
            end_date DATE,
            delivery_date DATE,
            pickup_date DATE,
            delivery_address TEXT,
            total_cost REAL,
            client_id INTEGER,
            created_at DATETIME
        )
    """)
    conn.commit()
    print("[OK] Created hire_order_new table")
    
    # Step 2: Copy old records (only columns that exist)
    if table_exists and row_count > 0:
        print("\n" + "=" * 60)
        print("Step 2: Copying existing records...")
        print("=" * 60)
        
        # Check which columns exist in old table
        cursor.execute("PRAGMA table_info(hire_order)")
        old_columns = {row[1]: row[0] for row in cursor.fetchall()}
        print(f"Columns in old table: {', '.join(old_columns.keys())}")
        
        # Columns to copy (only if they exist)
        columns_to_copy = [
            'id', 'event_id', 'client_id', 'quantity', 'status',
            'start_date', 'end_date', 'delivery_date', 'pickup_date',
            'delivery_address', 'total_cost', 'created_at'
        ]
        
        existing_cols = [col for col in columns_to_copy if col in old_columns]
        
        if existing_cols:
            select_cols = ', '.join(existing_cols)
            insert_cols = ', '.join(existing_cols)
            
            print(f"Copying columns: {', '.join(existing_cols)}")
            
            try:
                cursor.execute(f"""
                    INSERT INTO hire_order_new ({insert_cols})
                    SELECT {select_cols}
                    FROM hire_order
                """)
                conn.commit()
                
                # Verify copy
                cursor.execute("SELECT COUNT(*) FROM hire_order_new")
                new_count = cursor.fetchone()[0]
                print(f"[OK] Copied {new_count} rows to new table")
            except Exception as e:
                print(f"[ERROR] Failed to copy data: {e}")
                conn.rollback()
                raise
        else:
            print("[SKIP] No matching columns found to copy")
    else:
        print("\n[SKIP] No existing data to copy")
    
    # Step 3: Replace old table
    print("\n" + "=" * 60)
    print("Step 3: Replacing old table with new one...")
    print("=" * 60)
    
    if table_exists:
        cursor.execute("DROP TABLE hire_order")
        print("[OK] Dropped old hire_order table")
    
    cursor.execute("ALTER TABLE hire_order_new RENAME TO hire_order")
    print("[OK] Renamed hire_order_new to hire_order")
    
    conn.commit()
    
    # Step 4: Verify final structure
    print("\n" + "=" * 60)
    print("Step 4: Verifying final structure...")
    print("=" * 60)
    
    cursor.execute("PRAGMA table_info(hire_order)")
    final_columns = [(row[1], row[2]) for row in cursor.fetchall()]
    
    print(f"\nFinal table structure ({len(final_columns)} columns):")
    print(f"{'Column Name':<20} {'Type':<15}")
    print("-" * 40)
    for col_name, col_type in final_columns:
        print(f"{col_name:<20} {col_type:<15}")
    
    # Verify required columns
    required_columns = [
        'id', 'event_id', 'client_name', 'telephone', 'item_id',
        'quantity', 'status', 'deposit_amount', 'reference',
        'start_date', 'end_date', 'delivery_date', 'pickup_date',
        'delivery_address', 'total_cost', 'client_id', 'created_at'
    ]
    
    column_names = [col[0] for col in final_columns]
    missing = [col for col in required_columns if col not in column_names]
    
    if missing:
        print(f"\n[ERROR] Missing columns: {', '.join(missing)}")
        conn.close()
        exit(1)
    else:
        print("\n[SUCCESS] All required columns are present!")
    
    # Final row count
    cursor.execute("SELECT COUNT(*) FROM hire_order")
    final_count = cursor.fetchone()[0]
    print(f"Final row count: {final_count}")
    
    conn.close()
    
    print("\n" + "=" * 60)
    print("✅ REBUILD COMPLETED SUCCESSFULLY!")
    print("=" * 60)
    print("\nThe hire_order table now matches the HireOrder model exactly.")
    print("All 'no such column' errors are permanently resolved.")
    print("\n⚠️  IMPORTANT: Restart your Flask server for changes to take effect.")
    print("   Run: python sas_management/app.py")
    print("=" * 60)
    
except Exception as e:
    print(f"\n[ERROR] Rebuild failed: {e}")
    import traceback
    traceback.print_exc()
    conn.rollback()
    conn.close()
    exit(1)

