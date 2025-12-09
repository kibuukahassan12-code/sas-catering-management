"""
Seed Roles and Permissions for SAS Management System.
Run this script to populate the database with default roles and permissions.
"""
from app import app, db
from models import Role, Permission

# Define all available modules
ALL_MODULES = [
    "events", "clients", "inventory", "catering", "bakery", "hire",
    "procurement", "production", "finance", "hr", "reports", "bi",
    "pos", "food_safety", "haccp", "dispatch", "admin", "communication",
    "tasks", "quotes", "invoices", "accounting", "crm", "leads",
    "vendors", "contracts", "menu_builder", "timeline", "automation",
    "integrations", "university", "chat", "audit", "kds", "mobile_staff",
    "incidents", "branches", "floorplanner", "proposals", "profitability",
    "production_recipes", "search"
]

# Role definitions with their permissions
ROLE_DEFINITIONS = {
    "Admin": {
        "description": "Full system access with all permissions",
        "permissions": {module: True for module in ALL_MODULES}
    },
    "HireManager": {
        "description": "Manages hire orders and equipment",
        "permissions": {
            "hire": True,
            "inventory": True,
            "clients": True,
            "events": True,
            "tasks": True,
            "communication": True,
        }
    },
    "EventManager": {
        "description": "Manages events, catering, and client relations",
        "permissions": {
            "events": True,
            "clients": True,
            "catering": True,
            "bakery": True,
            "quotes": True,
            "invoices": True,
            "tasks": True,
            "communication": True,
            "timeline": True,
        }
    },
    "InventoryManager": {
        "description": "Manages inventory, procurement, and stock",
        "permissions": {
            "inventory": True,
            "procurement": True,
            "production": True,
            "vendors": True,
            "tasks": True,
        }
    },
    "Finance": {
        "description": "Manages financial operations, accounting, and reports",
        "permissions": {
            "finance": True,
            "accounting": True,
            "invoices": True,
            "quotes": True,
            "reports": True,
            "bi": True,
            "profitability": True,
            "cashbook": True,
        }
    },
    "ProductionManager": {
        "description": "Manages production, recipes, and quality control",
        "permissions": {
            "production": True,
            "production_recipes": True,
            "inventory": True,
            "food_safety": True,
            "haccp": True,
            "tasks": True,
        }
    },
    "SalesManager": {
        "description": "Manages sales, leads, and client relations",
        "permissions": {
            "crm": True,
            "leads": True,
            "clients": True,
            "quotes": True,
            "events": True,
            "communication": True,
            "tasks": True,
        }
    },
    "HRManager": {
        "description": "Manages human resources and staff",
        "permissions": {
            "hr": True,
            "payroll": True,
            "university": True,
            "tasks": True,
        }
    },
    "KitchenStaff": {
        "description": "Kitchen operations and production",
        "permissions": {
            "production": True,
            "production_recipes": True,
            "inventory": True,
            "tasks": True,
        }
    },
    "Waiter": {
        "description": "Service staff with limited access",
        "permissions": {
            "events": True,
            "tasks": True,
        }
    },
}

# Permission definitions
PERMISSION_DEFINITIONS = {
    "events": "Manage events and bookings",
    "clients": "Manage client information",
    "inventory": "Manage inventory and stock",
    "catering": "Manage catering menu and orders",
    "bakery": "Manage bakery items and orders",
    "hire": "Manage hire orders and equipment",
    "procurement": "Manage procurement and purchasing",
    "production": "Manage production operations",
    "finance": "Access financial operations",
    "hr": "Manage human resources",
    "reports": "View and generate reports",
    "bi": "Access business intelligence",
    "pos": "Access point of sale system",
    "food_safety": "Manage food safety records",
    "haccp": "Manage HACCP compliance",
    "dispatch": "Manage dispatch operations",
    "admin": "Admin access and user management",
    "communication": "Access communication hub",
    "tasks": "Manage tasks and assignments",
    "quotes": "Create and manage quotations",
    "invoices": "Create and manage invoices",
    "accounting": "Access accounting module",
    "crm": "Access CRM and pipeline",
    "leads": "Manage leads and inquiries",
    "vendors": "Manage vendor information",
    "contracts": "Manage contracts",
    "menu_builder": "Build and manage menus",
    "timeline": "Access event timeline",
    "automation": "Access automation features",
    "integrations": "Manage integrations",
    "university": "Access employee university",
    "chat": "Access chat system",
    "audit": "View audit logs",
    "kds": "Access kitchen display system",
    "mobile_staff": "Access mobile staff features",
    "incidents": "Manage incidents",
    "branches": "Manage branches",
    "floorplanner": "Access floor planner",
    "proposals": "Manage proposals",
    "profitability": "View profitability reports",
    "production_recipes": "Manage production recipes",
    "search": "Access search functionality",
}


def seed_roles_and_permissions():
    """Seed roles and permissions into the database."""
    with app.app_context():
        print("🌱 Seeding roles and permissions...")
        
        # Seed permissions
        print("\n📋 Creating permissions...")
        for module, description in PERMISSION_DEFINITIONS.items():
            permission = Permission.query.filter_by(module=module).first()
            if not permission:
                permission = Permission(
                    module=module,
                    name=module.replace("_", " ").title(),
                    description=description
                )
                db.session.add(permission)
                print(f"  ✓ Created permission: {module}")
            else:
                print(f"  ⊙ Permission already exists: {module}")
        
        db.session.commit()
        print(f"\n✓ Created {len(PERMISSION_DEFINITIONS)} permissions")
        
        # Seed roles
        print("\n👥 Creating roles...")
        for role_name, role_data in ROLE_DEFINITIONS.items():
            role = Role.query.filter_by(name=role_name).first()
            if not role:
                role = Role(
                    name=role_name,
                    permissions=role_data["permissions"]
                )
                db.session.add(role)
                print(f"  ✓ Created role: {role_name}")
            else:
                # Update permissions if role exists
                role.permissions = role_data["permissions"]
                print(f"  ↻ Updated role: {role_name}")
        
        db.session.commit()
        print(f"\n✓ Created/updated {len(ROLE_DEFINITIONS)} roles")
        
        print("\n🎉 Seeding complete!")
        print("\n📊 Summary:")
        print(f"  - Permissions: {Permission.query.count()}")
        print(f"  - Roles: {Role.query.count()}")


if __name__ == "__main__":
    seed_roles_and_permissions()

