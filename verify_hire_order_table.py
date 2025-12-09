"""Verify hire_order table structure matches the model."""
import sqlite3
import os

db_path = os.path.join("instance", "sas.db")

if os.path.exists(db_path):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    cursor.execute("PRAGMA table_info(hire_order)")
    columns = [(row[1], row[2], row[3]) for row in cursor.fetchall()]
    
    print("=" * 60)
    print("hire_order Table Structure")
    print("=" * 60)
    print(f"{'Column Name':<20} {'Type':<15} {'NotNull'}")
    print("-" * 60)
    for col in columns:
        not_null = "YES" if col[2] else "NO"
        print(f"{col[0]:<20} {col[1]:<15} {not_null}")
    
    # Check required columns
    column_names = [col[0] for col in columns]
    required = ['client_name', 'telephone', 'item_id', 'quantity', 'deposit_amount']
    missing = [col for col in required if col not in column_names]
    
    print("\n" + "=" * 60)
    if missing:
        print(f"⚠️  Missing columns: {', '.join(missing)}")
    else:
        print("✅ All required columns are present!")
    print("=" * 60)
    
    conn.close()
else:
    print(f"Database not found: {db_path}")

