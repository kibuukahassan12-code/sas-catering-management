#!/usr/bin/env python3
"""
Seed RBAC roles, permissions, and sample data.
Run this under your app environment.
"""
import os
import sys

# Add project root to path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

# Import app (created at module level)
import app
from models import db

app = app.app

# Try to import from new location, fallback to models
try:
    from app.models_and_rbac.rbac_models import Role, Permission
except ImportError:
    try:
        from models import Role, Permission
    except ImportError:
        print("⚠ Could not import Role/Permission models")
        Role = None
        Permission = None

with app.app_context():
    if not Role or not Permission:
        print("⚠ Role/Permission models not available, skipping RBAC seed")
    else:
        try:
            # Create tables if they don't exist
            db.create_all()
            
            # Check if already seeded
            if Role.query.filter_by(name="Admin").first():
                print("✓ RBAC already seeded")
            else:
                # Create permissions
                p1 = Permission(name="view_orders", description="View orders")
                p2 = Permission(name="manage_floorplans", description="Manage floor plans")
                p3 = Permission(name="manage_events", description="Manage events")
                p4 = Permission(name="manage_inventory", description="Manage inventory")
                
                # Create roles
                admin = Role(name="Admin", description="Full access")
                manager = Role(name="Manager", description="Manager access")
                staff = Role(name="Staff", description="Staff access")
                
                # Assign permissions
                admin.permissions = [p1, p2, p3, p4]
                manager.permissions = [p1, p3]
                staff.permissions = [p1]
                
                db.session.add_all([p1, p2, p3, p4, admin, manager, staff])
                db.session.commit()
                
                print("✓ Seeded RBAC roles and permissions:")
                print("  - Admin: all permissions")
                print("  - Manager: view_orders, manage_events")
                print("  - Staff: view_orders")
        except Exception as e:
            print(f"⚠ Error seeding RBAC: {e}")
            import traceback
            traceback.print_exc()
            db.session.rollback()
