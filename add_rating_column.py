#!/usr/bin/env python3
"""
Add rating column to hygiene_report table in all databases
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

print(f"Found {len(db_files)} database file(s)\n")

print("🔧 ADDING RATING COLUMN TO hygiene_report TABLE...\n")

# Check and fix each DB
for path in db_files:
    print(f"➡ Processing: {path}")
    try:
        conn = sqlite3.connect(path)
        cursor = conn.cursor()

        # Check if table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='hygiene_report'")
        exists = cursor.fetchone()

        if exists:
            print("   ✔ hygiene_report TABLE EXISTS")
            
            # Check current columns
            cursor.execute("PRAGMA table_info(hygiene_report)")
            columns = cursor.fetchall()
            column_names = [col[1] for col in columns]
            
            # Check if rating column exists
            if "rating" in column_names:
                print("   ✅ RATING COLUMN ALREADY EXISTS - No action needed")
            else:
                print("   ⚠️  RATING COLUMN MISSING - Adding now...")
                try:
                    cursor.execute("ALTER TABLE hygiene_report ADD COLUMN rating INTEGER")
                    conn.commit()
                    print("   ✅ SUCCESSFULLY ADDED rating column!")
                except Exception as e:
                    print(f"   ✗ ERROR adding column: {e}")
                    conn.rollback()
        else:
            print("   ℹ️  hygiene_report table does not exist yet (will be created with rating column when needed)")

        conn.close()
    except Exception as e:
        print(f"   ✗ ERROR: {e}")

    print("--------------------------------------------------")

print("\n✅ Database scan and fix complete!")

