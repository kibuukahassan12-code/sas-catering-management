"""
Seed Sample Users with Different Roles
Creates realistic sample users for testing and demonstration.
"""
import os
import sys
from datetime import datetime

# Add project root to path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from app import create_app
from models import User, Role, db

app = create_app()

def seed_sample_users():
    """Create sample users with different roles."""
    with app.app_context():
        print("=" * 60)
        print("Sample Users Seeding Script")
        print("=" * 60)
        
        # Get or create roles
        print("\n1. Checking roles...")
        roles = {}
        role_names = [
            "SuperAdmin", "Manager", "Finance", "Chef", 
            "EventPlanner", "HireManager", "SalesAgent", "Employee"
        ]
        
        for role_name in role_names:
            role = Role.query.filter_by(name=role_name).first()
            if role:
                roles[role_name] = role
                print(f"  ✓ Found role: {role_name}")
            else:
                print(f"  ⚠ Role '{role_name}' not found. Please run seed_rbac_complete.py first.")
        
        # Sample users data
        print("\n2. Creating sample users...")
        sample_users = [
            {
                "email": "admin@sasfoods.com",
                "role": "SuperAdmin",
                "description": "System Administrator"
            },
            {
                "email": "manager@sasfoods.com",
                "role": "Manager",
                "description": "Operations Manager"
            },
            {
                "email": "finance@sasfoods.com",
                "role": "Finance",
                "description": "Finance Manager"
            },
            {
                "email": "chef@sasfoods.com",
                "role": "Chef",
                "description": "Head Chef"
            },
            {
                "email": "eventplanner@sasfoods.com",
                "role": "EventPlanner",
                "description": "Event Coordinator"
            },
            {
                "email": "hire@sasfoods.com",
                "role": "HireManager",
                "description": "Equipment Hire Manager"
            },
            {
                "email": "sales@sasfoods.com",
                "role": "SalesAgent",
                "description": "Sales Representative"
            },
            {
                "email": "employee@sasfoods.com",
                "role": "Employee",
                "description": "General Employee"
            },
            {
                "email": "john.doe@sasfoods.com",
                "role": "Manager",
                "description": "Assistant Manager"
            },
            {
                "email": "jane.smith@sasfoods.com",
                "role": "EventPlanner",
                "description": "Senior Event Planner"
            },
            {
                "email": "mike.jones@sasfoods.com",
                "role": "Chef",
                "description": "Sous Chef"
            },
            {
                "email": "sarah.williams@sasfoods.com",
                "role": "SalesAgent",
                "description": "Senior Sales Agent"
            },
        ]
        
        created_count = 0
        updated_count = 0
        skipped_count = 0
        
        for user_data in sample_users:
            email = user_data["email"].lower().strip()
            role_name = user_data["role"]
            
            # Check if user exists
            existing_user = User.query.filter_by(email=email).first()
            
            if existing_user:
                # Update existing user's role if needed
                if role_name in roles:
                    if existing_user.role_id != roles[role_name].id:
                        existing_user.role_id = roles[role_name].id
                        db.session.commit()
                        updated_count += 1
                        print(f"  → Updated user: {email} (Role: {role_name})")
                    else:
                        skipped_count += 1
                        print(f"  - Skipped (already exists): {email}")
                else:
                    skipped_count += 1
                    print(f"  ⚠ Skipped (role not found): {email}")
            else:
                # Create new user
                if role_name not in roles:
                    print(f"  ⚠ Skipped (role '{role_name}' not found): {email}")
                    skipped_count += 1
                    continue
                
                # Generate a simple password (email prefix + "123")
                password = email.split("@")[0] + "123"
                
                user = User(
                    email=email,
                    must_change_password=True,
                    force_password_change=True
                )
                user.set_password(password)
                user.role_id = roles[role_name].id
                
                # Set legacy role enum (for backward compatibility)
                from models import UserRole
                role_enum_map = {
                    "SuperAdmin": UserRole.Admin,
                    "Manager": UserRole.Admin,
                    "Finance": UserRole.Admin,
                    "Chef": UserRole.KitchenStaff,
                    "EventPlanner": UserRole.Admin,
                    "HireManager": UserRole.HireManager,
                    "SalesAgent": UserRole.SalesManager,
                    "Employee": UserRole.Waiter
                }
                user.role = role_enum_map.get(role_name, UserRole.Admin)
                
                db.session.add(user)
                db.session.commit()
                created_count += 1
                print(f"  ✓ Created user: {email} (Role: {role_name}, Password: {password})")
        
        print("\n" + "=" * 60)
        print("Summary:")
        print(f"  ✓ Created: {created_count} users")
        print(f"  → Updated: {updated_count} users")
        print(f"  - Skipped: {skipped_count} users")
        print("=" * 60)
        print("\n📝 Login Credentials:")
        print("  All passwords follow the pattern: <email_prefix>123")
        print("  Example: admin@sasfoods.com → password: admin123")
        print("  Example: manager@sasfoods.com → password: manager123")
        print("\n⚠️  IMPORTANT: Users are created with 'must_change_password=True'")
        print("   They will be prompted to change password on first login.")
        print("=" * 60)

if __name__ == "__main__":
    seed_sample_users()

