"""
Fix missing price column in hire_order_item table.

This script specifically targets the hire_order_item table and ensures
all required columns exist, particularly the 'price' column.

Usage:
    python scripts/db_autofix/fix_missing_price.py
"""

import sqlite3
import os

DB_PATH = r"C:\Users\DELL\Desktop\sas management system\sas_management\instance\sas.db"

if not os.path.exists(DB_PATH):
    raise FileNotFoundError(f"DB NOT FOUND: {DB_PATH}")

conn = sqlite3.connect(DB_PATH)
cur = conn.cursor()

print("Checking if 'price' column exists in hire_order_item...")

cur.execute("PRAGMA table_info(hire_order_item)")
cols = [row[1] for row in cur.fetchall()]

if "price" not in cols:
    print("[FIX] Adding missing column: price REAL DEFAULT 0")
    cur.execute("ALTER TABLE hire_order_item ADD COLUMN price REAL DEFAULT 0")

if "subtotal" not in cols:
    print("[FIX] Adding missing column: subtotal REAL DEFAULT 0")
    cur.execute("ALTER TABLE hire_order_item ADD COLUMN subtotal REAL DEFAULT 0")

if "qty" not in cols:
    print("[FIX] Adding missing column: qty INTEGER DEFAULT 1")
    cur.execute("ALTER TABLE hire_order_item ADD COLUMN qty INTEGER DEFAULT 1")

conn.commit()
conn.close()

print("Completed. hire_order_item table is now updated.")

