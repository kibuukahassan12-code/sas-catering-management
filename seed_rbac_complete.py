"""
Complete RBAC Seeding Script for SAS Management System
Creates all roles, permissions, and assigns them correctly.
DOES NOT modify existing admin user login or password.
"""

from app import create_app, db
from models import Role, Permission, RolePermission, User

def seed_rbac_complete():
    """Seed complete RBAC structure."""
    app = create_app()
    
    with app.app_context():
        print("=" * 60)
        print("RBAC Complete Seeding Script")
        print("=" * 60)
        
        # 1. Create all roles
        print("\n1. Creating roles...")
        roles_data = [
            {"name": "SuperAdmin", "description": "Full system access - bypasses all permission checks"},
            {"name": "Manager", "description": "Management role with broad access"},
            {"name": "Finance", "description": "Finance and accounting access"},
            {"name": "Chef", "description": "Kitchen and catering management"},
            {"name": "EventPlanner", "description": "Event planning and coordination"},
            {"name": "HireManager", "description": "Equipment hire management"},
            {"name": "SalesAgent", "description": "Sales and CRM access"},
            {"name": "Employee", "description": "Basic employee access"},
        ]
        
        roles_dict = {}
        for role_data in roles_data:
            role = Role.query.filter_by(name=role_data["name"]).first()
            if not role:
                role = Role(name=role_data["name"], description=role_data["description"])
                db.session.add(role)
                print(f"  ✓ Created role: {role_data['name']}")
            else:
                # Update description if it exists
                if role.description != role_data["description"]:
                    role.description = role_data["description"]
                print(f"  → Role already exists: {role_data['name']}")
            roles_dict[role_data["name"]] = role
        
        db.session.commit()
        print(f"  ✓ Total roles: {len(roles_dict)}")
        
        # 2. Create all permissions
        print("\n2. Creating permissions...")
        permissions_data = [
            # Events permissions
            {"code": "events.view", "name": "View Events", "group": "events"},
            {"code": "events.edit", "name": "Edit Events", "group": "events"},
            {"code": "events.create", "name": "Create Events", "group": "events"},
            {"code": "events.delete", "name": "Delete Events", "group": "events"},
            {"code": "events.*", "name": "All Events", "group": "events"},
            
            # Catering permissions
            {"code": "catering.view", "name": "View Catering", "group": "catering"},
            {"code": "catering.edit", "name": "Edit Catering", "group": "catering"},
            {"code": "catering.*", "name": "All Catering", "group": "catering"},
            
            # Inventory permissions
            {"code": "inventory.view", "name": "View Inventory", "group": "inventory"},
            {"code": "inventory.edit", "name": "Edit Inventory", "group": "inventory"},
            {"code": "inventory.usage", "name": "Inventory Usage", "group": "inventory"},
            {"code": "inventory.*", "name": "All Inventory", "group": "inventory"},
            
            # CRM permissions
            {"code": "crm.view", "name": "View CRM", "group": "crm"},
            {"code": "crm.edit", "name": "Edit CRM", "group": "crm"},
            {"code": "crm.*", "name": "All CRM", "group": "crm"},
            
            # Leads permissions
            {"code": "leads.view", "name": "View Leads", "group": "leads"},
            {"code": "leads.edit", "name": "Edit Leads", "group": "leads"},
            {"code": "leads.*", "name": "All Leads", "group": "leads"},
            
            # Clients permissions
            {"code": "clients.view", "name": "View Clients", "group": "clients"},
            {"code": "clients.edit", "name": "Edit Clients", "group": "clients"},
            {"code": "clients.*", "name": "All Clients", "group": "clients"},
            
            # Finance permissions
            {"code": "finance.view", "name": "View Finance", "group": "finance"},
            {"code": "finance.edit", "name": "Edit Finance", "group": "finance"},
            {"code": "finance.*", "name": "All Finance", "group": "finance"},
            
            # Invoices permissions
            {"code": "invoices.view", "name": "View Invoices", "group": "invoices"},
            {"code": "invoices.edit", "name": "Edit Invoices", "group": "invoices"},
            {"code": "invoices.*", "name": "All Invoices", "group": "invoices"},
            
            # Expenses permissions
            {"code": "expenses.view", "name": "View Expenses", "group": "expenses"},
            {"code": "expenses.edit", "name": "Edit Expenses", "group": "expenses"},
            {"code": "expenses.*", "name": "All Expenses", "group": "expenses"},
            
            # Reporting permissions
            {"code": "reporting.view", "name": "View Reports", "group": "reporting"},
            {"code": "reporting.*", "name": "All Reporting", "group": "reporting"},
            
            # Hire permissions
            {"code": "hire.view", "name": "View Hire", "group": "hire"},
            {"code": "hire.edit", "name": "Edit Hire", "group": "hire"},
            {"code": "hire.*", "name": "All Hire", "group": "hire"},
            
            # Floorplans permissions
            {"code": "floorplans.view", "name": "View Floorplans", "group": "floorplans"},
            {"code": "floorplans.edit", "name": "Edit Floorplans", "group": "floorplans"},
            {"code": "floorplans.*", "name": "All Floorplans", "group": "floorplans"},
            
            # Tasks permissions
            {"code": "tasks.view", "name": "View Tasks", "group": "tasks"},
            {"code": "tasks.edit", "name": "Edit Tasks", "group": "tasks"},
            {"code": "tasks.*", "name": "All Tasks", "group": "tasks"},
            
            # Attendance permissions
            {"code": "attendance.view", "name": "View Attendance", "group": "attendance"},
            {"code": "attendance.edit", "name": "Edit Attendance", "group": "attendance"},
            {"code": "attendance.*", "name": "All Attendance", "group": "attendance"},
            
            # Profile permissions
            {"code": "profile.view", "name": "View Profile", "group": "profile"},
            {"code": "profile.edit", "name": "Edit Profile", "group": "profile"},
            {"code": "profile.*", "name": "All Profile", "group": "profile"},
            
            # Dashboard permission
            {"code": "dashboard.view", "name": "View Dashboard", "group": "dashboard"},
            
            # POS permission
            {"code": "pos.view", "name": "View POS", "group": "pos"},
            {"code": "pos.*", "name": "All POS", "group": "pos"},
            
            # Admin permission
            {"code": "admin.*", "name": "All Admin", "group": "admin"},
        ]
        
        permissions_dict = {}
        for perm_data in permissions_data:
            perm = Permission.query.filter_by(code=perm_data["code"]).first()
            if not perm:
                # Use group as module if module column exists
                module_value = perm_data.get("group") or perm_data.get("module")
                perm = Permission(
                    code=perm_data["code"],
                    name=perm_data.get("name", perm_data["code"]),
                    group=perm_data.get("group"),
                    description=perm_data.get("name", perm_data["code"])
                )
                # Set module if it exists in the model
                if hasattr(Permission, 'module'):
                    perm.module = module_value
                db.session.add(perm)
                print(f"  ✓ Created permission: {perm_data['code']}")
            else:
                # Update fields if they exist
                if perm.name != perm_data.get("name"):
                    perm.name = perm_data.get("name", perm_data["code"])
                if perm.group != perm_data.get("group"):
                    perm.group = perm_data.get("group")
                print(f"  → Permission already exists: {perm_data['code']}")
            permissions_dict[perm_data["code"]] = perm
        
        db.session.commit()
        print(f"  ✓ Total permissions: {len(permissions_dict)}")
        
        # 3. Assign permissions to roles
        print("\n3. Assigning permissions to roles...")
        
        # Clear existing role-permission mappings (but keep roles and permissions)
        RolePermission.query.delete()
        db.session.commit()
        
        role_permissions = {
            "SuperAdmin": [],  # SuperAdmin gets ALL permissions automatically via is_super_admin()
            
            "Manager": [
                "events.*",
                "catering.*",
                "inventory.*",
                "crm.*",
                "reporting.*",
            ],
            
            "Finance": [
                "finance.*",
                "invoices.*",
                "expenses.*",
                "reporting.*",
            ],
            
            "Chef": [
                "catering.view",
                "catering.edit",
                "inventory.usage",
            ],
            
            "EventPlanner": [
                "events.view",
                "events.edit",
                "floorplans.*",
                "clients.view",
            ],
            
            "HireManager": [
                "hire.*",
                "inventory.view",
            ],
            
            "SalesAgent": [
                "crm.*",
                "leads.*",
                "clients.*",
            ],
            
            "Employee": [
                "tasks.*",
                "attendance.*",
                "profile.*",
            ],
        }
        
        for role_name, perm_codes in role_permissions.items():
            role = roles_dict.get(role_name)
            if not role:
                print(f"  ✗ Role not found: {role_name}")
                continue
            
            for perm_code in perm_codes:
                perm = permissions_dict.get(perm_code)
                if not perm:
                    print(f"  ✗ Permission not found: {perm_code}")
                    continue
                
                # Check if mapping already exists
                existing = RolePermission.query.filter_by(
                    role_id=role.id,
                    permission_id=perm.id
                ).first()
                
                if not existing:
                    rp = RolePermission(role_id=role.id, permission_id=perm.id)
                    db.session.add(rp)
            
            print(f"  ✓ Assigned {len(perm_codes)} permissions to {role_name}")
        
        db.session.commit()
        
        # 4. Assign SuperAdmin role to existing admin user (if exists)
        print("\n4. Assigning SuperAdmin role to existing admin user...")
        superadmin_role = roles_dict.get("SuperAdmin")
        
        if not superadmin_role:
            print(f"  ✗ SuperAdmin role not found")
        else:
            # Find all users that might be admin
            admin_users = User.query.filter(
                (User.email.ilike('%admin%')) | 
                (User.email.ilike('%@sas%')) |
                (User.email.ilike('%@admin%'))
            ).all()
            
            if not admin_users:
                # Try to find any user with Admin role (legacy)
                admin_users = User.query.join(Role).filter(
                    Role.name.ilike('%admin%')
                ).all()
            
            if admin_users:
                for admin_user in admin_users:
                    # Only update if user doesn't already have SuperAdmin role
                    if admin_user.role_id != superadmin_role.id:
                        old_role = admin_user.role_obj.name if admin_user.role_obj else "None"
                        admin_user.role_id = superadmin_role.id
                        print(f"  ✓ Assigned SuperAdmin role to: {admin_user.email}")
                        print(f"    (Previous role: {old_role})")
                    else:
                        print(f"  → User {admin_user.email} already has SuperAdmin role")
                db.session.commit()
            else:
                print(f"  → No admin user found (this is OK if you haven't created one yet)")
                print(f"    You can manually assign SuperAdmin role to any user later")
        
        # 5. Summary
        print("\n" + "=" * 60)
        print("RBAC Seeding Complete!")
        print("=" * 60)
        print(f"Roles created: {len(roles_dict)}")
        print(f"Permissions created: {len(permissions_dict)}")
        
        # Count role-permission mappings
        total_mappings = RolePermission.query.count()
        print(f"Role-Permission mappings: {total_mappings}")
        
        print("\n✓ RBAC structure is ready!")
        print("✓ SuperAdmin bypasses all permission checks")
        print("✓ All roles and permissions are configured")
        
        return True

if __name__ == "__main__":
    try:
        seed_rbac_complete()
    except Exception as e:
        print(f"\n✗ Error: {e}")
        import traceback
        traceback.print_exc()
        exit(1)

