"""
Script to fix user roles and permissions
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from sas_management.app import create_app
from sas_management.models import User, Role, Permission, db, RolePermission

def fix_user_permissions():
    app = create_app()
    
    with app.app_context():
        print("=" * 60)
        print("FIXING USER ROLES AND PERMISSIONS")
        print("=" * 60)
        
        # Find the user
        user = User.query.filter_by(email='kibuekahassan12@gmail.com').first()
        if not user:
            # Try other email variations
            user = User.query.filter(User.email.like('%kibuuka%')).first()
        
        if user:
            print(f"\nUser: {user.email} (ID: {user.id})")
            print(f"Current role_id: {user.role_id}")
            
            # Find or create the proper Accounting role
            accounting_role = Role.query.filter(
                (Role.name == 'Accounting') | (Role.name == 'ACCOUNTING')
            ).first()
            
            if accounting_role:
                print(f"Found Accounting role: {accounting_role.name} (ID: {accounting_role.id})")
                
                # Check if the role has the required permissions
                perms = list(accounting_role.permissions)
                perm_codes = [p.code for p in perms]
                print(f"\nCurrent permissions ({len(perms)}):")
                for p in perms:
                    print(f"  - {p.code}: {p.name}")
                
                # Add required accounting permissions if missing
                required_perms = [
                    'accounting.view_accounting',
                    'accounting.create_invoice', 
                    'accounting.approve_payments',
                    'accounting.view_reports'
                ]
                
                for perm_code in required_perms:
                    if perm_code not in perm_codes:
                        # Find or create the permission
                        perm = Permission.query.filter_by(code=perm_code).first()
                        if not perm:
                            # Try to find by name
                            perm_name = perm_code.split('.')[-1].replace('_', ' ').title()
                            perm = Permission.query.filter_by(name=perm_name).first()
                        
                        if perm:
                            # Add the permission to the role
                            role_perm = RolePermission(role_id=accounting_role.id, permission_id=perm.id)
                            # Check if already exists
                            existing = RolePermission.query.filter_by(
                                role_id=accounting_role.id, 
                                permission_id=perm.id
                            ).first()
                            if not existing:
                                db.session.add(role_perm)
                                print(f"  [ADDED] {perm_code} to role")
                            else:
                                print(f"  [EXISTS] {perm_code}")
                        else:
                            print(f"  [NOT FOUND] {perm_code}")
                
                # Update user role to use the proper Accounting role
                if user.role_id != accounting_role.id:
                    user.role_id = accounting_role.id
                    print(f"\n[UPDATED] User role_id changed from {user.role_id} to {accounting_role.id}")
                else:
                    print(f"\n[OK] User already has correct role_id")
                
                db.session.commit()
                print("\n[SUCCESS] User permissions updated!")
            else:
                print("ERROR: Accounting role not found!")
        else:
            print("ERROR: User not found!")
        
        # List all users and their roles
        print("\n" + "=" * 60)
        print("ALL USERS:")
        print("=" * 60)
        users = User.query.all()
        for u in users:
            role_name = "None"
            if u.role_obj:
                role_name = u.role_obj.name
            print(f"  {u.email}: {role_name} (role_id={u.role_id})")
        
        print("\n" + "=" * 60)
        print("ALL ROLES:")
        print("=" * 60)
        roles = Role.query.all()
        for r in roles:
            perm_count = len(list(r.permissions)) if r.permissions else 0
            print(f"  {r.id}: {r.name} ({perm_count} permissions)")

if __name__ == "__main__":
    fix_user_permissions()
