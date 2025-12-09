"""Check if POS tables exist."""
import sqlite3
import os

db_path = os.path.join("instance", "site.db")
if os.path.exists(db_path):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Check for POS tables
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name LIKE 'pos%'")
    tables = cursor.fetchall()
    
    print("POS Tables found:")
    for table in tables:
        print(f"  - {table[0]}")
    
    if not tables:
        print("\n⚠ No POS tables found! Need to create them.")
    else:
        # Check table structure
        for table in tables:
            table_name = table[0]
            cursor.execute(f"PRAGMA table_info({table_name})")
            columns = cursor.fetchall()
            print(f"\n{table_name} columns:")
            for col in columns:
                print(f"  - {col[1]} ({col[2]})")
    
    conn.close()
else:
    print(f"Database not found at {db_path}")

