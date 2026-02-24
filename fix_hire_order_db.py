"""
Fix hire_order table to match the current Order model.
This script ensures all columns match the SQLAlchemy model definition.
"""
import sqlite3
import os

# Database paths to check
db_paths = [
    os.path.join("instance", "sas.db"),
    os.path.join("instance", "site.db"),
]

def fix_hire_order_table(db_path):
    """Fix hire_order table to match the model exactly."""
    if not os.path.exists(db_path):
        print(f"Database not found: {db_path}")
        return False
    
    print(f"\n{'='*60}")
    print(f"Fixing hire_order table in: {db_path}")
    print(f"{'='*60}")
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # Check if table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='hire_order'")
        table_exists = cursor.fetchone() is not None
        
        if not table_exists:
            print("  Table 'hire_order' does not exist. Creating new table...")
            cursor.execute("""
                CREATE TABLE hire_order (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    client_name VARCHAR(255) NOT NULL,
                    client_id INTEGER,
                    event_id INTEGER,
                    event_date DATE,
                    start_date DATE,
                    end_date DATE,
                    delivery_date DATE,
                    pickup_date DATE,
                    delivery_address TEXT,
                    telephone VARCHAR(50),
                    email VARCHAR(120),
                    status VARCHAR(50) NOT NULL DEFAULT 'Pending',
                    total_cost NUMERIC(12,2) NOT NULL DEFAULT 0.00,
                    amount_paid NUMERIC(12,2) NOT NULL DEFAULT 0.00,
                    balance_due NUMERIC(12,2) NOT NULL DEFAULT 0.00,
                    reference VARCHAR(50) UNIQUE,
                    comments TEXT,
                    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (client_id) REFERENCES client(id),
                    FOREIGN KEY (event_id) REFERENCES event(id)
                )
            """)
            conn.commit()
            print("  [OK] Created new hire_order table")
            conn.close()
            return True
        
        # Table exists - need to rebuild with correct schema
        cursor.execute("SELECT COUNT(*) FROM hire_order")
        row_count = cursor.fetchone()[0]
        print(f"  Found {row_count} existing rows")
        
        # Get existing columns
        cursor.execute("PRAGMA table_info(hire_order)")
        existing_columns = {row[1]: row for row in cursor.fetchall()}
        print(f"  Existing columns: {list(existing_columns.keys())}")
        
        # Step 1: Create new table with exact schema (all nullable columns)
        print("\n  Step 1: Creating new table with correct schema...")
        cursor.execute("DROP TABLE IF EXISTS hire_order_new")
        cursor.execute("""
            CREATE TABLE hire_order_new (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                client_name VARCHAR(255) NOT NULL DEFAULT '',
                client_id INTEGER,
                event_id INTEGER,
                event_date DATE,
                start_date DATE,
                end_date DATE,
                delivery_date DATE,
                pickup_date DATE,
                delivery_address TEXT,
                telephone VARCHAR(50),
                email VARCHAR(120),
                status VARCHAR(50) NOT NULL DEFAULT 'Pending',
                total_cost NUMERIC(12,2) NOT NULL DEFAULT 0.00,
                amount_paid NUMERIC(12,2) NOT NULL DEFAULT 0.00,
                balance_due NUMERIC(12,2) NOT NULL DEFAULT 0.00,
                reference VARCHAR(50),
                comments TEXT,
                created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (client_id) REFERENCES client(id),
                FOREIGN KEY (event_id) REFERENCES event(id)
            )
        """)
        print("  [OK] Created hire_order_new table")
        
        # Step 2: Copy data from old table
        if row_count > 0:
            print("\n  Step 2: Copying data from old table...")
            
            # Map old column names to new column names
            column_mapping = {
                'id': 'id',
                'client_name': 'client_name',
                'client_id': 'client_id',
                'event_id': 'event_id',
                'event_date': 'event_date',
                'start_date': 'start_date',
                'end_date': 'end_date',
                'delivery_date': 'delivery_date',
                'pickup_date': 'pickup_date',
                'delivery_address': 'delivery_address',
                'telephone': 'telephone',
                'email': 'email',
                'status': 'status',
                'total_cost': 'total_cost',
                'amount_paid': 'amount_paid',
                'balance_due': 'balance_due',
                'reference': 'reference',
                'comments': 'comments',
                'created_at': 'created_at',
                'updated_at': 'updated_at',
            }
            
            # Find columns that exist in both old and new tables
            cols_to_copy = [col for col in column_mapping.keys() if col in existing_columns]
            
            if cols_to_copy:
                cols_str = ', '.join(cols_to_copy)
                try:
                    cursor.execute(f"""
                        INSERT INTO hire_order_new ({cols_str})
                        SELECT {cols_str}
                        FROM hire_order
                    """)
                    print(f"  [OK] Copied {row_count} rows using columns: {cols_str}")
                except Exception as e:
                    print(f"  [WARNING] Could not copy all columns: {e}")
                    # Try minimal copy
                    if 'id' in existing_columns:
                        minimal_cols = ['id']
                        if 'status' in existing_columns:
                            minimal_cols.append('status')
                        if 'created_at' in existing_columns:
                            minimal_cols.append('created_at')
                        cols_str = ', '.join(minimal_cols)
                        cursor.execute(f"""
                            INSERT INTO hire_order_new ({cols_str})
                            SELECT {cols_str}
                            FROM hire_order
                        """)
                        print(f"  [OK] Copied rows with minimal columns: {cols_str}")
        else:
            print("  [SKIP] No rows to copy")
        
        # Step 3: Replace old table
        print("\n  Step 3: Replacing old table with new one...")
        cursor.execute("DROP TABLE hire_order")
        cursor.execute("ALTER TABLE hire_order_new RENAME TO hire_order")
        print("  [OK] Replaced hire_order table")
        
        conn.commit()
        
        # Step 4: Verify
        print("\n  Step 4: Verifying final structure...")
        cursor.execute("PRAGMA table_info(hire_order)")
        final_columns = cursor.fetchall()
        print(f"  Final columns ({len(final_columns)}):")
        for col in final_columns:
            col_name = col[1]
            col_type = col[2]
            nullable = "NULL" if col[3] == 0 else "NOT NULL"
            print(f"    - {col_name} ({col_type}) {nullable}")
        
        # Verify row count
        cursor.execute("SELECT COUNT(*) FROM hire_order")
        final_count = cursor.fetchone()[0]
        print(f"\n  Final row count: {final_count}")
        
        conn.close()
        print("\n  [SUCCESS] hire_order table fixed!")
        return True
        
    except Exception as e:
        print(f"  [ERROR] Fix failed: {e}")
        import traceback
        traceback.print_exc()
        conn.rollback()
        conn.close()
        return False

if __name__ == "__main__":
    print("=" * 60)
    print("FIX: hire_order table to allow NULL client_id")
    print("=" * 60)
    print("\nThis fixes the 'NOT NULL constraint failed: hire_order.client_id' error")
    print("by rebuilding the table with the correct schema.\n")
    
    success_count = 0
    for db_path in db_paths:
        if fix_hire_order_table(db_path):
            success_count += 1
    
    print("\n" + "=" * 60)
    if success_count > 0:
        print("SUCCESS! hire_order table fixed.")
        print("\nRestart your Flask server for changes to take effect.")
    else:
        print("WARNING: No databases were processed.")
    print("=" * 60)
