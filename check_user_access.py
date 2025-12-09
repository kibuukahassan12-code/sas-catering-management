"""
Quick script to check user access and grant admin if needed.
"""
from app import create_app
from models import User, Role, db
from sqlalchemy import func

app = create_app()

with app.app_context():
    print("="*60)
    print("USER ACCESS CHECK")
    print("="*60)
    
    # Get all users
    users = User.query.order_by(User.id.asc()).all()
    
    if not users:
        print("No users found in database.")
    else:
        print(f"\nFound {len(users)} user(s):\n")
        
        for user in users:
            print(f"User ID: {user.id}")
            print(f"Email: {user.email}")
            
            # Check role
            if user.role_obj:
                print(f"Role: {user.role_obj.name}")
                print(f"Is SuperAdmin: {user.is_super_admin()}")
            else:
                print("Role: None")
                print(f"Is SuperAdmin: {user.is_super_admin()}")
            
            # Check if first user
            if user.id == 1:
                print("✓ FIRST USER - Should have automatic admin access")
            
            print("-" * 60)
        
        # Check if SuperAdmin role exists
        superadmin_role = Role.query.filter(func.lower(Role.name) == "superadmin").first()
        if superadmin_role:
            print(f"\n✓ SuperAdmin role exists (ID: {superadmin_role.id})")
            users_with_superadmin = User.query.filter_by(role_id=superadmin_role.id).all()
            if users_with_superadmin:
                print(f"Users with SuperAdmin role:")
                for u in users_with_superadmin:
                    print(f"  - {u.email} (ID: {u.id})")
            else:
                print("No users assigned to SuperAdmin role")
        else:
            print("\n⚠ SuperAdmin role does not exist")
            print("Run: python grant_admin_access.py")
        
        print("\n" + "="*60)
        print("RECOMMENDATIONS:")
        print("="*60)
        
        first_user = User.query.filter_by(id=1).first()
        if first_user:
            print(f"✓ First user exists: {first_user.email}")
            print("  This user should automatically have admin access.")
            if not first_user.is_super_admin():
                print("  ⚠ But is_super_admin() returns False - this is a bug!")
        else:
            print("⚠ No first user (ID=1) found")
        
        print("\nTo grant admin access, run:")
        if users:
            print(f"  python grant_admin_access.py {users[0].email}")
        else:
            print("  python grant_admin_access.py your-email@example.com")

