"""Fix hire_order table in the correct database location."""
import sqlite3
import os

# The actual database location used by the Flask app
db_path = os.path.join("sas_management", "instance", "sas.db")

if not os.path.exists(db_path):
    print(f"Database not found: {db_path}")
    exit(1)

print(f"Fixing database: {db_path}")

conn = sqlite3.connect(db_path)
cursor = conn.cursor()

try:
    # Get current row count
    cursor.execute("SELECT COUNT(*) FROM hire_order")
    row_count = cursor.fetchone()[0]
    print(f"Current rows: {row_count}")
    
    # Get existing columns
    cursor.execute("PRAGMA table_info(hire_order)")
    old_cols = [row[1] for row in cursor.fetchall()]
    print(f"Existing columns: {old_cols}")

    # Create new table with correct schema (client_id is NULLABLE)
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
    print("Created new table with nullable client_id")

    # Copy existing data if any
    if row_count > 0:
        # Handle columns that need special treatment for NULL values
        new_cols = ['id', 'client_name', 'client_id', 'event_id', 'event_date', 'start_date', 
                    'end_date', 'delivery_date', 'pickup_date', 'delivery_address', 'telephone',
                    'email', 'status', 'total_cost', 'amount_paid', 'balance_due', 'reference',
                    'comments', 'created_at', 'updated_at']
        common = [c for c in new_cols if c in old_cols]
        
        # Build SELECT with COALESCE for NOT NULL columns
        select_parts = []
        for c in common:
            if c == 'client_name':
                select_parts.append("COALESCE(client_name, 'Unknown Client')")
            elif c == 'status':
                select_parts.append("COALESCE(status, 'Pending')")
            elif c == 'total_cost':
                select_parts.append("COALESCE(total_cost, 0.00)")
            elif c == 'amount_paid':
                select_parts.append("COALESCE(amount_paid, 0.00)")
            elif c == 'balance_due':
                select_parts.append("COALESCE(balance_due, 0.00)")
            elif c == 'created_at':
                select_parts.append("COALESCE(created_at, CURRENT_TIMESTAMP)")
            elif c == 'updated_at':
                select_parts.append("COALESCE(updated_at, CURRENT_TIMESTAMP)")
            else:
                select_parts.append(c)
        
        cols_str = ', '.join(common)
        select_str = ', '.join(select_parts)
        cursor.execute(f"INSERT INTO hire_order_new ({cols_str}) SELECT {select_str} FROM hire_order")
        print(f"Copied {row_count} rows")

    # Replace old table
    cursor.execute("DROP TABLE hire_order")
    cursor.execute("ALTER TABLE hire_order_new RENAME TO hire_order")
    conn.commit()
    print("Replaced old table")

    # Verify - check client_id is now nullable
    cursor.execute("PRAGMA table_info(hire_order)")
    print("\nNew schema:")
    for row in cursor.fetchall():
        col_name = row[1]
        not_null = "NOT NULL" if row[3] == 1 else "NULLABLE"
        print(f"  {col_name}: {not_null}")
        if col_name == 'client_id':
            if row[3] == 0:
                print("    >>> client_id is now NULLABLE - FIX SUCCESSFUL!")
            else:
                print("    >>> ERROR: client_id is still NOT NULL!")

    conn.close()
    print("\nDone! Please restart your Flask server.")

except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
    conn.rollback()
    conn.close()
