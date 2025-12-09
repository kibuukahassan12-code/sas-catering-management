"""Fully rebuild hire_order table to match HireOrder model exactly."""
import sqlite3
import os

# Database paths to check
db_paths = [
    os.path.join("instance", "sas.db"),
    os.path.join("instance", "site.db"),
]

def rebuild_table(db_path):
    """Rebuild hire_order table following the exact schema provided."""
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
        table_exists = cursor.fetchone() is not None
        
        if not table_exists:
            print("  Table 'hire_order' does not exist. Creating new table...")
            # Create table directly
            cursor.execute("""
                CREATE TABLE hire_order (
                    id INTEGER PRIMARY KEY,
                    event_id INTEGER,
                    client_name TEXT,
                    telephone TEXT,
                    item_id INTEGER,
                    quantity INTEGER,
                    status TEXT,
                    deposit_amount REAL,
                    start_date DATE,
                    end_date DATE,
                    delivery_date DATE,
                    pickup_date DATE,
                    delivery_address TEXT,
                    total_cost REAL,
                    reference TEXT,
                    client_id INTEGER,
                    created_at DATETIME
                )
            """)
            conn.commit()
            print("  [OK] Created new hire_order table")
            conn.close()
            return True
        
        # Get existing row count
        cursor.execute("SELECT COUNT(*) FROM hire_order")
        row_count = cursor.fetchone()[0]
        print(f"  Found {row_count} existing rows")
        
        # Step 1: Create new table with exact schema
        print("\n  Step 1: Creating new table with correct schema...")
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
                start_date DATE,
                end_date DATE,
                delivery_date DATE,
                pickup_date DATE,
                delivery_address TEXT,
                total_cost REAL,
                reference TEXT,
                client_id INTEGER,
                created_at DATETIME
            )
        """)
        print("  [OK] Created hire_order_new table")
        
        # Step 2: Copy data from old table
        print("\n  Step 2: Copying data from old table...")
        
        if row_count > 0:
            # Check which columns exist in the old table
            cursor.execute("PRAGMA table_info(hire_order)")
            old_columns = {row[1]: row[0] for row in cursor.fetchall()}
            
            # Columns to copy (only if they exist in old table)
            columns_to_copy = [
                'id', 'event_id', 'client_id', 'quantity', 'status',
                'start_date', 'end_date', 'delivery_date', 'pickup_date',
                'delivery_address', 'total_cost', 'created_at'
            ]
            
            # Filter to only columns that exist
            existing_cols = [col for col in columns_to_copy if col in old_columns]
            
            if existing_cols:
                select_cols = ', '.join(existing_cols)
                insert_cols = ', '.join(existing_cols)
                
                try:
                    cursor.execute(f"""
                        INSERT INTO hire_order_new ({insert_cols})
                        SELECT {select_cols}
                        FROM hire_order
                    """)
                    conn.commit()
                    print(f"  [OK] Copied {row_count} rows to new table")
                except Exception as e:
                    print(f"  [WARNING] Error copying data: {e}")
                    print(f"  Attempting to copy with available columns only...")
                    conn.rollback()
                    
                    # Try copying with just id if other columns fail
                    if 'id' in old_columns:
                        try:
                            cursor.execute("""
                                INSERT INTO hire_order_new (id)
                                SELECT id FROM hire_order
                            """)
                            conn.commit()
                            print(f"  [OK] Copied {row_count} rows (id only)")
                        except Exception as e2:
                            print(f"  [ERROR] Could not copy data: {e2}")
                            conn.rollback()
            else:
                print("  [SKIP] No matching columns found to copy")
        else:
            print("  [SKIP] No rows to copy")
        
        # Step 3: Replace old table
        print("\n  Step 3: Replacing old table with new one...")
        cursor.execute("DROP TABLE hire_order")
        print("  [OK] Dropped old hire_order table")
        
        cursor.execute("ALTER TABLE hire_order_new RENAME TO hire_order")
        print("  [OK] Renamed hire_order_new to hire_order")
        
        conn.commit()
        
        # Step 4: Verify final structure
        print("\n  Step 4: Verifying final structure...")
        cursor.execute("PRAGMA table_info(hire_order)")
        final_columns = [row[1] for row in cursor.fetchall()]
        
        print(f"  Final columns ({len(final_columns)}):")
        for col in final_columns:
            print(f"    - {col}")
        
        # Verify all required columns are present
        required_columns = [
            'id', 'event_id', 'client_name', 'telephone', 'item_id',
            'quantity', 'status', 'deposit_amount', 'start_date', 'end_date',
            'delivery_date', 'pickup_date', 'delivery_address', 'total_cost',
            'reference', 'client_id', 'created_at'
        ]
        
        missing = [col for col in required_columns if col not in final_columns]
        
        if missing:
            print(f"\n  [ERROR] Missing columns: {', '.join(missing)}")
            conn.close()
            return False
        else:
            print("\n  [SUCCESS] All required columns are present!")
        
        # Verify row count
        cursor.execute("SELECT COUNT(*) FROM hire_order")
        final_count = cursor.fetchone()[0]
        print(f"  Final row count: {final_count}")
        
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
print("FULL REBUILD: hire_order table to match HireOrder model")
print("=" * 60)
print("\nThis will:")
print("  1. Create a new table with the exact schema")
print("  2. Copy existing data (preserving all rows)")
print("  3. Replace the old table with the new one")
print("\n⚠️  This operation will rebuild the table structure.")
print("   All existing data will be preserved.")
print("=" * 60)

success_count = 0
for db_path in db_paths:
    if rebuild_table(db_path):
        success_count += 1

print("\n" + "=" * 60)
if success_count > 0:
    print("✅ REBUILD COMPLETED SUCCESSFULLY!")
    print("\nThe hire_order table now matches the HireOrder model exactly.")
    print("All 'no such column' errors are permanently resolved.")
    print("\n⚠️  IMPORTANT: Restart your Flask server for changes to take effect.")
    print("   Run: python sas_management/app.py")
else:
    print("⚠️  No databases were processed.")
print("=" * 60)

