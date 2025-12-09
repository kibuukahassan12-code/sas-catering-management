"""
Seed RBAC System: Roles, Permissions, and Role-Permission assignments.
Run this script to populate the database with default roles and permissions.
"""
from app import app, db
from models import Role, Permission, RolePermission, User, UserRole

# Define all permissions in module.action format
PERMISSIONS = [
    # Dashboard
    ("dashboard", "view", "View dashboard"),
    
    # Orders
    ("orders", "create", "Create orders"),
    ("orders", "edit", "Edit orders"),
    ("orders", "delete", "Delete orders"),
    ("orders", "view", "View orders"),
    
    # Events
    ("events", "manage", "Manage events (create, edit, delete)"),
    ("events", "view", "View events"),
    
    # Staff
    ("staff", "manage", "Manage staff assignments"),
    ("staff", "view", "View staff information"),
    
    # Finance
    ("finance", "view", "View financial information"),
    ("finance", "manage", "Manage financial operations"),
    
    # Inventory
    ("inventory", "manage", "Manage inventory"),
    ("inventory", "view", "View inventory"),
    
    # Production
    ("production", "manage", "Manage production operations"),
    ("production", "view", "View production information"),
    
    # Communication
    ("communication", "access", "Access communication hub"),
    
    # Admin
    ("admin", "manage", "Manage system administration"),
    ("admin", "view", "View admin panel"),
]

# Role definitions with their permissions
ROLE_DEFINITIONS = {
    "Super Admin": {
        "description": "Full system access with all permissions",
        "permissions": [p[0] + "." + p[1] for p in PERMISSIONS]  # All permissions
    },
    "Manager": {
        "description": "Management role with broad access",
        "permissions": [
            "dashboard.view",
            "orders.create", "orders.edit", "orders.view",
            "events.manage", "events.view",
            "staff.manage", "staff.view",
            "finance.view",
            "inventory.view",
            "production.view",
            "communication.access",
        ]
    },
    "Chef": {
        "description": "Kitchen and production management",
        "permissions": [
            "dashboard.view",
            "orders.view",
            "events.view",
            "inventory.manage", "inventory.view",
            "production.manage", "production.view",
        ]
    },
    "Waiter": {
        "description": "Service staff with limited access",
        "permissions": [
            "dashboard.view",
            "orders.view",
            "events.view",
            "staff.view",
        ]
    },
    "Accountant": {
        "description": "Financial operations and reporting",
        "permissions": [
            "dashboard.view",
            "orders.view",
            "finance.view", "finance.manage",
        ]
    },
    "Store Manager": {
        "description": "Inventory and store management",
        "permissions": [
            "dashboard.view",
            "orders.view", "orders.create", "orders.edit",
            "inventory.manage", "inventory.view",
            "production.view",
        ]
    },
    "Basic Staff": {
        "description": "Basic staff with minimal access",
        "permissions": [
            "dashboard.view",
            "orders.view",
        ]
    },
}


def seed_rbac():
    """Seed roles, permissions, and role-permission assignments."""
    with app.app_context():
        print("🌱 Seeding RBAC System...")
        print("=" * 60)
        
        # Step 1: Create Permissions
        print("\n📋 Step 1: Creating Permissions...")
        permission_map = {}
        for module, action, description in PERMISSIONS:
            permission_name = f"{module}.{action}"
            permission = Permission.query.filter_by(name=permission_name).first()
            if not permission:
                permission = Permission(
                    name=permission_name,
                    module=module,
                    action=action
                )
                db.session.add(permission)
                print(f"  ✓ Created permission: {permission_name}")
            else:
                # Update if exists
                permission.module = module
                permission.action = action
                print(f"  ↻ Updated permission: {permission_name}")
            permission_map[permission_name] = permission
        
        db.session.commit()
        print(f"\n✓ Total permissions: {Permission.query.count()}")
        
        # Step 2: Create Roles
        print("\n👥 Step 2: Creating Roles...")
        role_map = {}
        for role_name, role_data in ROLE_DEFINITIONS.items():
            role = Role.query.filter_by(name=role_name).first()
            if not role:
                role = Role(
                    name=role_name,
                    description=role_data["description"]
                )
                db.session.add(role)
                db.session.flush()  # Get the ID
                print(f"  ✓ Created role: {role_name}")
            else:
                role.description = role_data["description"]
                print(f"  ↻ Updated role: {role_name}")
            role_map[role_name] = role
        
        db.session.commit()
        print(f"\n✓ Total roles: {Role.query.count()}")
        
        # Step 3: Assign Permissions to Roles
        print("\n🔗 Step 3: Assigning Permissions to Roles...")
        for role_name, role_data in ROLE_DEFINITIONS.items():
            role = role_map[role_name]
            
            # Remove existing permissions for this role
            RolePermission.query.filter_by(role_id=role.id).delete()
            
            # Assign new permissions
            assigned_count = 0
            for permission_name in role_data["permissions"]:
                if permission_name in permission_map:
                    permission = permission_map[permission_name]
                    # Check if already exists
                    existing = RolePermission.query.filter_by(
                        role_id=role.id,
                        permission_id=permission.id
                    ).first()
                    if not existing:
                        rp = RolePermission(
                            role_id=role.id,
                            permission_id=permission.id
                        )
                        db.session.add(rp)
                        assigned_count += 1
            
            db.session.commit()
            print(f"  ✓ {role_name}: {assigned_count} permissions assigned")
        
        print(f"\n✓ Total role-permission assignments: {RolePermission.query.count()}")
        
        # Step 4: Assign Super Admin role to existing Admin users
        print("\n👤 Step 4: Assigning Super Admin role to existing Admin users...")
        super_admin_role = role_map.get("Super Admin")
        if super_admin_role:
            admin_users = User.query.filter_by(role=UserRole.Admin).all()
            for user in admin_users:
                if not user.role_id:
                    user.role_id = super_admin_role.id
                    print(f"  ✓ Assigned Super Admin role to {user.email}")
        
        db.session.commit()
        
        print("\n" + "=" * 60)
        print("🎉 RBAC Seeding Complete!")
        print("\n📊 Summary:")
        print(f"  - Permissions: {Permission.query.count()}")
        print(f"  - Roles: {Role.query.count()}")
        print(f"  - Role-Permission Assignments: {RolePermission.query.count()}")
        print("\n✅ You can now use the admin panel to manage roles and permissions.")


if __name__ == "__main__":
    seed_rbac()

