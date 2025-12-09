#!/usr/bin/env python3
"""
Fix DB schema for user, vehicle, floor_plan, seating_assignment and add missing columns.
Run this under your app environment (FLASK_APP or using project import).
"""
import os
import sys
from datetime import datetime
from sqlalchemy import text

# Add project root to path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

# Import app (created at module level)
import app
from models import db

app = app.app

with app.app_context():
    with db.engine.connect() as conn:
        # Helper to add column safely if missing
        def add_column_if_missing(table, column_def, check_expr):
            try:
                res = conn.execute(text(f"SELECT {check_expr} FROM {table} LIMIT 1"))
                print(f"✓ {table}: column exists -> {check_expr}")
            except Exception as e:
                print(f"➡ {table}: adding column {column_def}")
                try:
                    conn.execute(text(f"ALTER TABLE {table} ADD COLUMN {column_def}"))
                    conn.commit()
                    print(f"✓ Added {column_def} to {table}")
                except Exception as e2:
                    print(f"⚠ Error adding column to {table}: {e2}")
                    conn.rollback()
        
        # User columns
        add_column_if_missing("user", "role_id INTEGER", "role_id")
        add_column_if_missing("user", "force_password_change BOOLEAN DEFAULT 0", "force_password_change")
        
        # Vehicle columns
        try:
            add_column_if_missing("vehicle", "updated_at TEXT", "updated_at")
        except:
            print("⚠ vehicle table may not exist, skipping")
        
        # Floor plan columns
        try:
            add_column_if_missing("floor_plan", "json_layout TEXT DEFAULT '{}'", "json_layout")
            add_column_if_missing("floor_plan", "created_by INTEGER", "created_by")
            add_column_if_missing("floor_plan", "updated_at TEXT", "updated_at")
        except:
            print("⚠ floor_plan table may not exist, skipping")
        
        # Seating assignment
        try:
            add_column_if_missing("seating_assignment", "seat_number TEXT", "seat_number")
            add_column_if_missing("seating_assignment", "special_requests TEXT", "special_requests")
            add_column_if_missing("seating_assignment", "updated_at TEXT", "updated_at")
        except:
            print("⚠ seating_assignment table may not exist, skipping")
    
    print("✓ DB column checks complete.")

