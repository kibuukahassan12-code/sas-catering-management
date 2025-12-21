import sqlite3
import os

DB_PATH = r"C:\Users\DELL\Desktop\sas management system\sas_management\instance\sas.db"

conn = sqlite3.connect(DB_PATH)
cur = conn.cursor()

cur.execute("PRAGMA table_info(hire_order_item)")
cols = [row[1] for row in cur.fetchall()]

print(f"Current columns in hire_order_item: {cols}")

fixes = []

if "qty" not in cols:
    fixes.append(("qty", "INTEGER DEFAULT 1"))

if "subtotal" not in cols:
    fixes.append(("subtotal", "REAL DEFAULT 0"))

for col, coltype in fixes:
    print(f"[FIX] Adding missing column: {col} {coltype}")
    cur.execute(f"ALTER TABLE hire_order_item ADD COLUMN {col} {coltype}")

conn.commit()
conn.close()

print("Completed hire_order_item full check.")

