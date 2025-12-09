"""
RBAC Seed Script - Auto-generate default system permissions and roles.
"""
from app import create_app, db
from models import Role, Permission, RolePermission

app = create_app()

# Default permissions list
DEFAULT_PERMISSIONS = [
    ("view_users", "Can view user list"),
    ("add_users", "Create new users"),
    ("assign_roles", "Assign roles to users"),
    ("view_financials", "Access finance module"),
    ("manage_inventory", "Full inventory rights"),
    ("view_inventory", "See stock levels"),
    ("manage_events", "Edit/Create events"),
    ("view_events", "Basic event viewing"),
    ("manage_hires", "Manage hire department"),
    ("view_hires", "View hire orders"),
    ("system_admin", "Full unrestricted access")
]

# Role permission mappings
ROLE_PERMISSIONS = {
    "SuperAdmin": [
        "view_users", "add_users", "assign_roles", "view_financials",
        "manage_inventory", "view_inventory", "manage_events", "view_events",
        "manage_hires", "view_hires", "system_admin"
    ],
    "Admin": [
        "view_users", "add_users", "assign_roles", "view_financials",
        "manage_inventory", "view_inventory", "manage_events", "view_events",
        "manage_hires", "view_hires"
    ],
    "Manager": [
        "view_users", "view_financials", "manage_inventory", "view_inventory",
        "manage_events", "view_events", "manage_hires", "view_hires"
    ],
    "Staff": [
        "view_inventory", "view_events", "view_hires"
    ]
}

def seed_rbac():
    """Seed permissions and roles."""
    with app.app_context():
        print("🌱 Seeding RBAC system...")
        
        # Step 1: Create permissions
        print("\n📋 Creating permissions...")
        permission_map = {}
        for perm_name, perm_desc in DEFAULT_PERMISSIONS:
            permission = Permission.query.filter_by(name=perm_name).first()
            if not permission:
                permission = Permission(name=perm_name, description=perm_desc)
                db.session.add(permission)
                print(f"  ✓ Created permission: {perm_name}")
            else:
                permission.description = perm_desc
                print(f"  ↻ Updated permission: {perm_name}")
            permission_map[perm_name] = permission
        
        db.session.commit()
        print(f"\n✓ Total permissions: {Permission.query.count()}")
        
        # Step 2: Create roles and assign permissions
        print("\n👥 Creating roles and assigning permissions...")
        for role_name, perm_names in ROLE_PERMISSIONS.items():
            # Create or get role
            role = Role.query.filter_by(name=role_name).first()
            if not role:
                role = Role(name=role_name, description=f"{role_name} role")
                db.session.add(role)
                db.session.flush()
                print(f"  ✓ Created role: {role_name}")
            else:
                print(f"  ↻ Using existing role: {role_name}")
            
            # Clear existing permissions
            RolePermission.query.filter_by(role_id=role.id).delete()
            
            # Assign permissions
            for perm_name in perm_names:
                if perm_name in permission_map:
                    permission = permission_map[perm_name]
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
            
            db.session.commit()
            print(f"    → Assigned {len(perm_names)} permissions to {role_name}")
        
        print("\n✅ RBAC seeding complete!")
        print(f"  - Permissions: {Permission.query.count()}")
        print(f"  - Roles: {Role.query.count()}")
        print(f"  - Role-Permission assignments: {RolePermission.query.count()}")

if __name__ == "__main__":
    seed_rbac()

