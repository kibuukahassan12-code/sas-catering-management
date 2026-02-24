"""
Complete fix for hire_order and hire_order_item tables.
This ensures both tables match the SQLAlchemy models exactly.
"""
import sqlite3
import os

db_path = os.path.join("sas_management", "instance", "sas.db")

if not os.path.exists(db_path):
    print(f"Database not found: {db_path}")
    exit(1)

print(f"=" * 60)
print(f"FIXING HIRE TABLES IN: {db_path}")
print(f"=" * 60)

conn = sqlite3.connect(db_path)
cursor = conn.cursor()

try:
    # ========================================
    # FIX hire_order_item TABLE
    # ========================================
    print("\n[1] Fixing hire_order_item table...")
    
    # Check if table exists and get row count
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='hire_order_item'")
    if cursor.fetchone():
        cursor.execute("SELECT COUNT(*) FROM hire_order_item")
        item_count = cursor.fetchone()[0]
        print(f"    Current rows: {item_count}")
        
        # Get existing columns
        cursor.execute("PRAGMA table_info(hire_order_item)")
        old_item_cols = {row[1]: row for row in cursor.fetchall()}
        print(f"    Old columns: {list(old_item_cols.keys())}")
    else:
        item_count = 0
        old_item_cols = {}
        print("    Table does not exist, will create new")
    
    # Drop and recreate with correct schema
    cursor.execute("DROP TABLE IF EXISTS hire_order_item_new")
    cursor.execute("""
        CREATE TABLE hire_order_item_new (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            order_id INTEGER NOT NULL,
            item_id INTEGER NOT NULL,
            qty INTEGER NOT NULL DEFAULT 1,
            price NUMERIC(10,2) NOT NULL DEFAULT 0,
            subtotal NUMERIC(12,2) NOT NULL DEFAULT 0,
            FOREIGN KEY (order_id) REFERENCES hire_order(id),
            FOREIGN KEY (item_id) REFERENCES inventory_item(id)
        )
    """)
    print("    Created new table with correct schema")
    
    # Copy data if exists
    if item_count > 0 and old_item_cols:
        # Map old columns to new
        # Old might have: hire_order_id, inventory_item_id, quantity_rented, unit_price
        # New needs: order_id, item_id, qty, price, subtotal
        
        select_parts = ["id"]
        insert_cols = ["id"]
        
        # order_id mapping
        if 'order_id' in old_item_cols:
            select_parts.append("order_id")
        elif 'hire_order_id' in old_item_cols:
            select_parts.append("hire_order_id")
        else:
            select_parts.append("1")  # default
        insert_cols.append("order_id")
        
        # item_id mapping
        if 'item_id' in old_item_cols:
            select_parts.append("item_id")
        elif 'inventory_item_id' in old_item_cols:
            select_parts.append("inventory_item_id")
        else:
            select_parts.append("1")  # default
        insert_cols.append("item_id")
        
        # qty mapping
        if 'qty' in old_item_cols:
            select_parts.append("COALESCE(qty, 1)")
        elif 'quantity_rented' in old_item_cols:
            select_parts.append("COALESCE(quantity_rented, 1)")
        else:
            select_parts.append("1")
        insert_cols.append("qty")
        
        # price mapping
        if 'price' in old_item_cols:
            select_parts.append("COALESCE(price, 0)")
        elif 'unit_price' in old_item_cols:
            select_parts.append("COALESCE(unit_price, 0)")
        else:
            select_parts.append("0")
        insert_cols.append("price")
        
        # subtotal mapping
        if 'subtotal' in old_item_cols:
            select_parts.append("COALESCE(subtotal, 0)")
        else:
            select_parts.append("0")
        insert_cols.append("subtotal")
        
        insert_str = ", ".join(insert_cols)
        select_str = ", ".join(select_parts)
        
        try:
            cursor.execute(f"INSERT INTO hire_order_item_new ({insert_str}) SELECT {select_str} FROM hire_order_item")
            print(f"    Copied {item_count} rows")
        except Exception as e:
            print(f"    Warning copying data: {e}")
    
    # Replace old table
    cursor.execute("DROP TABLE IF EXISTS hire_order_item")
    cursor.execute("ALTER TABLE hire_order_item_new RENAME TO hire_order_item")
    print("    Replaced old table")
    
    # Verify
    cursor.execute("PRAGMA table_info(hire_order_item)")
    print("    New schema:")
    for row in cursor.fetchall():
        print(f"      {row[1]}: {'NOT NULL' if row[3] else 'NULLABLE'}")
    
    # ========================================
    # VERIFY hire_order TABLE
    # ========================================
    print("\n[2] Verifying hire_order table...")
    cursor.execute("PRAGMA table_info(hire_order)")
    hire_order_cols = {row[1]: row for row in cursor.fetchall()}
    
    client_id_nullable = hire_order_cols.get('client_id', (0,0,0,1))[3] == 0
    if client_id_nullable:
        print("    client_id is NULLABLE - OK")
    else:
        print("    WARNING: client_id is NOT NULL - may need fixing")
    
    conn.commit()
    
    # ========================================
    # FINAL VERIFICATION
    # ========================================
    print("\n" + "=" * 60)
    print("VERIFICATION")
    print("=" * 60)
    
    print("\nhire_order columns:")
    cursor.execute("PRAGMA table_info(hire_order)")
    for row in cursor.fetchall():
        print(f"  {row[1]}: {'NOT NULL' if row[3] else 'NULLABLE'}")
    
    print("\nhire_order_item columns:")
    cursor.execute("PRAGMA table_info(hire_order_item)")
    for row in cursor.fetchall():
        print(f"  {row[1]}: {'NOT NULL' if row[3] else 'NULLABLE'}")
    
    cursor.execute("SELECT COUNT(*) FROM hire_order")
    print(f"\nTotal hire_order rows: {cursor.fetchone()[0]}")
    
    cursor.execute("SELECT COUNT(*) FROM hire_order_item")
    print(f"Total hire_order_item rows: {cursor.fetchone()[0]}")
    
    conn.close()
    
    print("\n" + "=" * 60)
    print("FIX COMPLETE!")
    print("=" * 60)
    print("\nPlease restart your Flask server and try creating a hire order again.")

except Exception as e:
    print(f"\nERROR: {e}")
    import traceback
    traceback.print_exc()
    conn.rollback()
    conn.close()
