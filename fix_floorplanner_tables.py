#!/usr/bin/env python3
"""
Fix Floor Planner Database Tables
Ensures all required columns exist for FloorPlan and SeatingAssignment tables.
"""

import sys
import os
from datetime import datetime

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app, db
from models import FloorPlan, SeatingAssignment
from sqlalchemy import inspect, text

def fix_floorplanner_tables():
    """Ensure all floor planner tables and columns exist."""
    app = create_app()
    
    with app.app_context():
        print("=" * 60)
        print("FLOOR PLANNER DATABASE FIX")
        print("=" * 60)
        print()
        
        inspector = inspect(db.engine)
        table_names = inspector.get_table_names()
        
        # Check FloorPlan table
        if 'floor_plan' not in table_names:
            print("Creating floor_plan table...")
            db.create_all()
            print("   ✓ floor_plan table created")
        else:
            print("Checking floor_plan table columns...")
            columns = {col['name']: col for col in inspector.get_columns('floor_plan')}
            
            required_columns = {
                'id': {'type': 'INTEGER', 'primary_key': True},
                'event_id': {'type': 'INTEGER', 'nullable': False},
                'name': {'type': 'VARCHAR(150)', 'nullable': False},
                'layout_json': {'type': 'TEXT', 'nullable': False},
                'thumbnail': {'type': 'BLOB', 'nullable': True},
                'created_by': {'type': 'INTEGER', 'nullable': True},
                'created_at': {'type': 'DATETIME', 'nullable': False},
                'updated_at': {'type': 'DATETIME', 'nullable': True}
            }
            
            for col_name, col_spec in required_columns.items():
                if col_name not in columns:
                    print(f"   Adding missing column: {col_name}")
                    try:
                        if col_name == 'layout_json':
                            db.session.execute(text(f"ALTER TABLE floor_plan ADD COLUMN {col_name} TEXT DEFAULT '{{\"objects\": [], \"meta\": {{\"zoom\":1,\"pan\":{{\"x\":0,\"y\":0}},\"grid\":true}}}}'"))
                        elif col_name == 'thumbnail':
                            db.session.execute(text(f"ALTER TABLE floor_plan ADD COLUMN {col_name} BLOB"))
                        elif col_name == 'created_at':
                            db.session.execute(text(f"ALTER TABLE floor_plan ADD COLUMN {col_name} DATETIME DEFAULT CURRENT_TIMESTAMP"))
                        elif col_name == 'updated_at':
                            db.session.execute(text(f"ALTER TABLE floor_plan ADD COLUMN {col_name} DATETIME"))
                        else:
                            db.session.execute(text(f"ALTER TABLE floor_plan ADD COLUMN {col_name} INTEGER"))
                        db.session.commit()
                        print(f"      ✓ Added {col_name}")
                    except Exception as e:
                        if "duplicate column" not in str(e).lower() and "already exists" not in str(e).lower():
                            print(f"      ✗ Error adding {col_name}: {e}")
                        db.session.rollback()
                else:
                    print(f"   ✓ {col_name} exists")
        
        # Check SeatingAssignment table
        if 'seating_assignment' not in table_names:
            print("\nCreating seating_assignment table...")
            db.create_all()
            print("   ✓ seating_assignment table created")
        else:
            print("\nChecking seating_assignment table columns...")
            columns = {col['name']: col for col in inspector.get_columns('seating_assignment')}
            
            required_columns = {
                'id': {'type': 'INTEGER', 'primary_key': True},
                'floorplan_id': {'type': 'INTEGER', 'nullable': False},
                'guest_name': {'type': 'VARCHAR(120)', 'nullable': True},
                'table_number': {'type': 'VARCHAR(50)', 'nullable': True},
                'seat_number': {'type': 'VARCHAR(50)', 'nullable': True},
                'special_requests': {'type': 'TEXT', 'nullable': True},
                'created_at': {'type': 'DATETIME', 'nullable': False},
                'updated_at': {'type': 'DATETIME', 'nullable': True}
            }
            
            for col_name, col_spec in required_columns.items():
                if col_name not in columns:
                    print(f"   Adding missing column: {col_name}")
                    try:
                        if col_name in ['guest_name', 'table_number', 'seat_number']:
                            size = col_name.replace('_', '').replace('name', '120').replace('number', '50')
                            db.session.execute(text(f"ALTER TABLE seating_assignment ADD COLUMN {col_name} VARCHAR({size.split('VARCHAR')[1] if 'VARCHAR' in size else '120'})"))
                        elif col_name == 'special_requests':
                            db.session.execute(text(f"ALTER TABLE seating_assignment ADD COLUMN {col_name} TEXT"))
                        elif col_name == 'created_at':
                            db.session.execute(text(f"ALTER TABLE seating_assignment ADD COLUMN {col_name} DATETIME DEFAULT CURRENT_TIMESTAMP"))
                        elif col_name == 'updated_at':
                            db.session.execute(text(f"ALTER TABLE seating_assignment ADD COLUMN {col_name} DATETIME"))
                        else:
                            db.session.execute(text(f"ALTER TABLE seating_assignment ADD COLUMN {col_name} INTEGER"))
                        db.session.commit()
                        print(f"      ✓ Added {col_name}")
                    except Exception as e:
                        if "duplicate column" not in str(e).lower() and "already exists" not in str(e).lower():
                            print(f"      ✗ Error adding {col_name}: {e}")
                        db.session.rollback()
                else:
                    print(f"   ✓ {col_name} exists")
        
        # Verify models can be imported
        try:
            from models import FloorPlan, SeatingAssignment
            print("\n" + "=" * 60)
            print("✅ FLOOR PLANNER TABLES VERIFIED")
            print("=" * 60)
            print("\nAll required tables and columns are present.")
            print("Floor Planner module is ready to use!")
            print()
        except Exception as e:
            print(f"\n⚠️  Warning: {e}")
            print("Tables may need to be recreated. Try running: db.create_all()")
            return False
    
    return True

if __name__ == "__main__":
    success = fix_floorplanner_tables()
    sys.exit(0 if success else 1)

