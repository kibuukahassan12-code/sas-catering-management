"""Verify MenuPackage and Event models have required fields."""
import os
import sys

project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

import app
from models import MenuPackage, Event

app_instance = app.app

with app_instance.app_context():
    print("=" * 60)
    print("Schema Verification")
    print("=" * 60)
    
    # Check MenuPackage
    print("\n📦 MenuPackage Model:")
    mp_columns = {c.name: str(c.type) for c in MenuPackage.__table__.columns}
    required_mp = ['id', 'name', 'price_per_guest', 'description', 'items', 'created_at', 'updated_at']
    for col in required_mp:
        if col in mp_columns:
            print(f"  ✅ {col}: {mp_columns[col]}")
        else:
            print(f"  ❌ {col}: MISSING")
    
    # Check Event
    print("\n📅 Event Model:")
    event_columns = {c.name: str(c.type) for c in Event.__table__.columns}
    required_event = ['id', 'client_name', 'event_type', 'event_date', 'quoted_value', 'status', 'menu_package_id']
    for col in required_event:
        if col in event_columns:
            print(f"  ✅ {col}: {event_columns[col]}")
        else:
            print(f"  ❌ {col}: MISSING")
    
    print("\n" + "=" * 60)
    print("✅ Schema verification complete!")
    print("=" * 60)

