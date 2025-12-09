"""
Script to grant full admin access to a user.
This creates a SuperAdmin role with all permissions and assigns it to the specified user.
"""
from app import create_app
from models import User, Role, Permission, RolePermission, db
from sqlalchemy import func

def grant_admin_access(user_email=None):
    """Grant SuperAdmin access to a user."""
    app = create_app()
    
    with app.app_context():
        # Find or create SuperAdmin role
        superadmin_role = Role.query.filter(func.lower(Role.name) == "superadmin").first()
        
        if not superadmin_role:
            print("Creating SuperAdmin role...")
            superadmin_role = Role(
                name="SuperAdmin",
                description="Super Administrator with full system access"
            )
            db.session.add(superadmin_role)
            db.session.flush()
            print("✓ SuperAdmin role created")
        else:
            print("✓ SuperAdmin role already exists")
        
        # Get all permissions and assign them to SuperAdmin
        all_permissions = Permission.query.all()
        existing_permission_ids = {p.id for p in superadmin_role.permissions}
        
        new_permissions_count = 0
        for perm in all_permissions:
            if perm.id not in existing_permission_ids:
                superadmin_role.permissions.append(perm)
                new_permissions_count += 1
        
        if new_permissions_count > 0:
            print(f"✓ Assigned {new_permissions_count} permissions to SuperAdmin role")
        else:
            print(f"✓ SuperAdmin role already has all {len(all_permissions)} permissions")
        
        db.session.commit()
        
        # Find user to grant access
        if user_email:
            user = User.query.filter(func.lower(User.email) == user_email.lower()).first()
        else:
            # Get the first user if no email specified
            user = User.query.first()
            if user:
                user_email = user.email
                print(f"No email specified, using first user: {user_email}")
        
        if not user:
            print(f"❌ User not found: {user_email}")
            print("\nAvailable users:")
            users = User.query.all()
            for u in users:
                print(f"  - {u.email}")
            return False
        
        # Assign SuperAdmin role to user
        if user.role_id != superadmin_role.id:
            user.role_id = superadmin_role.id
            db.session.commit()
            print(f"✓ SuperAdmin role assigned to: {user.email}")
        else:
            print(f"✓ User {user.email} already has SuperAdmin role")
        
        print("\n" + "="*60)
        print("✅ ADMIN ACCESS GRANTED SUCCESSFULLY!")
        print("="*60)
        print(f"User: {user.email}")
        print(f"Role: {superadmin_role.name}")
        print(f"Permissions: {len(superadmin_role.permissions)}")
        print("\nYou now have full access to all system features.")
        print("="*60)
        
        return True

if __name__ == "__main__":
    import sys
    
    # Get email from command line argument if provided
    email = sys.argv[1] if len(sys.argv) > 1 else None
    
    if email:
        print(f"Granting admin access to: {email}")
    else:
        print("="*60)
        print("GRANT ADMIN ACCESS")
        print("="*60)
        print("\nNo email specified. Options:")
        print("1. Run with your email: python grant_admin_access.py your-email@example.com")
        print("2. Or the script will use the first user in the database")
        print("\n" + "="*60 + "\n")
        
        # Show all users
        app = create_app()
        with app.app_context():
            users = User.query.all()
            if users:
                print("Available users:")
                for i, u in enumerate(users, 1):
                    role_name = u.role_obj.name if u.role_obj else "No role"
                    print(f"  {i}. {u.email} (Role: {role_name})")
                print()
    
    grant_admin_access(email)

