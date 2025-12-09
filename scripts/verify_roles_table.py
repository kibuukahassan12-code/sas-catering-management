"""Verify roles table has correct columns."""
import os
import sys
from sqlalchemy import inspect, text

project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

import app
from models import Role, db

app_instance = app.app

with app_instance.app_context():
    print("=" * 60)
    print("Roles Table Verification")
    print("=" * 60)
    
    inspector = inspect(db.engine)
    
    if 'roles' not in inspector.get_table_names():
        print("❌ Roles table does not exist!")
        print("Creating table...")
        db.create_all()
        print("✅ Table created.")
    else:
        print("✅ Roles table exists")
    
    # Get columns
    columns = {col['name']: str(col['type']) for col in inspector.get_columns('roles')}
    
    print("\n📋 Current columns:")
    for col_name, col_type in columns.items():
        print(f"  - {col_name}: {col_type}")
    
    # Check required columns
    required = ['id', 'name', 'description', 'created_at', 'updated_at']
    print("\n✅ Required columns check:")
    for col in required:
        if col in columns:
            print(f"  ✅ {col}")
        else:
            print(f"  ❌ {col}: MISSING")
    
    print("\n" + "=" * 60)

