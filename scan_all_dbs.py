#!/usr/bin/env python3
"""
Scan project for all .db files and check hygiene_report table structure
"""

import os
import sqlite3

project_root = r"C:\Users\DELL\Desktop\sas management system"

print("🔍 SCANNING FOR ALL DATABASE FILES...\n")

db_files = []

# Find all .db files
for root, dirs, files in os.walk(project_root):
    for f in files:
        if f.endswith(".db"):
            full_path = os.path.join(root, f)
            db_files.append(full_path)

# List found DBs
for path in db_files:
    print(f"FOUND DB: {path}")

print(f"\nTotal .db files found: {len(db_files)}\n")

print("🔎 CHECKING hygiene_report TABLE IN EACH DATABASE...\n")

# Check each DB for hygiene_report
for path in db_files:
    print(f"➡ Checking: {path}")
    try:
        conn = sqlite3.connect(path)
        cursor = conn.cursor()

        # Check if table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='hygiene_report'")
        exists = cursor.fetchone()

        if exists:
            print("   ✔ hygiene_report TABLE EXISTS HERE!")
            print("   Columns:")
            cursor.execute("PRAGMA table_info(hygiene_report)")
            columns = cursor.fetchall()
            for col in columns:
                print("      ", col)
            
            # Check specifically for rating column
            rating_exists = any(col[1] == "rating" for col in columns)
            if rating_exists:
                print("   ✅ RATING COLUMN EXISTS!")
            else:
                print("   ⚠️  RATING COLUMN MISSING!")
        else:
            print("   ✖ hygiene_report NOT found in this DB.")

        conn.close()
    except Exception as e:
        print("   ERROR:", e)

    print("--------------------------------------------------")

