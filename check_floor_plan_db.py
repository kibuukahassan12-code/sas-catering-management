#!/usr/bin/env python3
"""Check floor_plan table structure and data."""

print("=== ACTIVE DATABASE ===")

from app import app
import os

with app.app_context():
    print("SQLALCHEMY_DATABASE_URI:", app.config["SQLALCHEMY_DATABASE_URI"])
    
    print("\n=== FLOOR_PLAN TABLE STRUCTURE ===")
    
    import sqlite3
    db_uri = app.config["SQLALCHEMY_DATABASE_URI"]
    
    # Handle both relative and absolute paths
    if db_uri.startswith("sqlite:///"):
        db_path = db_uri.replace("sqlite:///", "")
        # If it's a relative path, check instance folder first
        if not os.path.isabs(db_path):
            instance_path = os.path.join("instance", "site.db")
            if os.path.exists(instance_path):
                db_path = os.path.abspath(instance_path)
            else:
                db_path = os.path.abspath(db_path)
        else:
            db_path = os.path.abspath(db_path)
    
    print(f"Database path: {db_path}")
    print(f"Database exists: {os.path.exists(db_path)}")
    
    if not os.path.exists(db_path):
        print(f"\nERROR: Database file not found at {db_path}")
        # Try instance/site.db
        instance_path = os.path.abspath(os.path.join("instance", "site.db"))
        if os.path.exists(instance_path):
            print(f"Trying instance path: {instance_path}")
            db_path = instance_path
        else:
            print("ERROR: No database file found!")
            exit(1)
    
    conn = sqlite3.connect(db_path)
    
    # Check if table exists
    tables = [row[0] for row in conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()]
    print(f"\nTables in database: {tables}")
    
    if "floor_plan" in tables:
        rows = conn.execute("PRAGMA table_info(floor_plan)").fetchall()
        print("\nColumn info:")
        for r in rows:
            print(r)
        
        print("\n=== FIRST THREE ROWS FROM FLOOR_PLAN ===")
        try:
            rows = conn.execute("SELECT * FROM floor_plan LIMIT 3").fetchall()
            if rows:
                for r in rows:
                    print(r)
            else:
                print("No rows found in floor_plan table")
        except Exception as e:
            print("ERROR:", e)
    else:
        print("\nERROR: floor_plan table does not exist!")
    
    conn.close()

