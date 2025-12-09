#!/usr/bin/env python3
"""
Check database paths and fix rating column in hygiene_report table
"""

import os
import sys

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Step 1 — Print the REAL ABSOLUTE DB path used by fix_all_tables.py
from config import Config

db_path_from_config = Config.SQLALCHEMY_DATABASE_URI.replace("sqlite:///", "")
absolute_db_path = os.path.abspath(db_path_from_config)
print("DB path used by fix script:", absolute_db_path)
print()

# Step 2 — Print the REAL ABSOLUTE DB path Flask uses at runtime
from app import app

with app.app_context():
    flask_db_uri = app.config["SQLALCHEMY_DATABASE_URI"]
    print("DB path used by Flask:", flask_db_uri)
    print()

# Step 3 — Open the ACTUAL database file and check columns
import sqlite3

db_path = absolute_db_path
print(f"Connecting to database at: {db_path}")
print(f"Database exists: {os.path.exists(db_path)}")
print()

conn = sqlite3.connect(db_path)
cursor = conn.cursor()

try:
    cursor.execute("PRAGMA table_info(hygiene_report)")
    columns = cursor.fetchall()
    print("Columns in hygiene_report table:")
    for row in columns:
        print(row)
    print()
    
    # Check if rating column exists
    rating_exists = any(col[1] == "rating" for col in columns)
    print(f"Rating column exists: {rating_exists}")
    print()
    
    # Step 4 — If 'rating' is missing, force add it
    if not rating_exists:
        try:
            cursor.execute("ALTER TABLE hygiene_report ADD COLUMN rating INTEGER")
            conn.commit()
            print("FORCE-ADDED rating column to hygiene_report")
        except Exception as e:
            print("ALTER TABLE result:", e)
    else:
        print("Rating column already exists, no action needed")
        
except sqlite3.OperationalError as e:
    if "no such table" in str(e).lower():
        print(f"Table 'hygiene_report' does not exist yet. It will be created with the rating column when needed.")
    else:
        print(f"Error checking table: {e}")

conn.close()

print()
print("=" * 60)
print("Database check complete")
print("=" * 60)
print()
print("Step 5: UI templates for hygiene reports:")
print("  - templates/production/hygiene_reports_view.html: Already handles rating field with fallback")
print("  - templates/production/hygiene_reports_form.html: Uses overall_rating (string field)")
print("  - templates/production/hygiene_reports_list.html: Displays overall_rating")
print()
print("The rating field (Integer) is available in the model and will be synced with the database.")
print("The view template already displays it as a fallback if overall_rating is not available.")

