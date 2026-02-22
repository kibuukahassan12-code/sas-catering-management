"""
Setup script to create Hire Manager user and assign them to manage the Hire department.
Run this script to set up the Hire department with a Hire Manager.
"""
from sas_management.app import create_app, db
from sas_management.models import User, Role, Department, Employee, Permission, RolePermission
import secrets
import string

def setup_hire_manager():
    app = create_app()
    
    with app.app_context():
        print("=" * 60)
        print("Hire Manager Setup Script")
        print("=" * 60)
        
        # 1. Ensure HireManager role exists
        print("\n1. Checking HireManager role...")
        hire_manager_role = Role.query.filter_by(name="HireManager").first()
        if not hire_manager_role:
            hire_manager_role = Role(
                name="HireManager",
                description="Equipment Hire Manager - manages hire department operations"
            )
            db.session.add(hire_manager_role)
            db.session.commit()
            print("  [OK] Created HireManager role")
        else:
            print("  [--] HireManager role already exists")
        
        # 1.5. Assign permissions to HireManager role
        print("\n1b. Assigning hire permissions to HireManager role...")
        hire_permissions = ["manage_hires", "view_hires", "manage_hire", "view_hire"]
        for perm_name in hire_permissions:
            perm = Permission.query.filter_by(name=perm_name).first()
            if not perm:
                perm = Permission(code=perm_name, name=perm_name, description=f"Permission for {perm_name}")
                db.session.add(perm)
                db.session.commit()
            
            existing_rp = RolePermission.query.filter_by(
                role_id=hire_manager_role.id,
                permission_id=perm.id
            ).first()
            if not existing_rp:
                rp = RolePermission(role_id=hire_manager_role.id, permission_id=perm.id)
                db.session.add(rp)
        db.session.commit()
        print(f"  [OK] Assigned {len(hire_permissions)} permissions to HireManager role")
        
        # 2. Create Hire department if not exists
        print("\n2. Checking Hire department...")
        hire_dept = Department.query.filter_by(name="Hire").first()
        if not hire_dept:
            hire_dept = Department(
                name="Hire",
                description="Equipment Hire Department - manages equipment rental and maintenance"
            )
            db.session.add(hire_dept)
            db.session.commit()
            print("  [OK] Created Hire department")
        else:
            print("  [--] Hire department already exists")
        
        # 3. Check if HireManager user already exists
        print("\n3. Checking for existing Hire Manager user...")
        hire_manager_email = "hiremanager@sas.com"
        hire_manager_user = User.query.filter_by(email=hire_manager_email).first()
        temp_password = None
        
        if hire_manager_user:
            print(f"  [--] Hire Manager user already exists: {hire_manager_user.email}")
            # Update their role to HireManager if not already
            if hire_manager_user.role_id != hire_manager_role.id:
                hire_manager_user.role_id = hire_manager_role.id
                db.session.commit()
                print("  [OK] Updated user role to HireManager")
        else:
            # Generate a secure temporary password
            print(f"\n4. Creating Hire Manager user...")
            temp_password = "".join(secrets.choice(string.ascii_letters + string.digits + "!@#$%^&*") for _ in range(12))
            
            hire_manager_user = User(
                email=hire_manager_email,
                must_change_password=True,
                force_password_change=True,
                first_login=True
            )
            hire_manager_user.set_password(temp_password, is_temporary=True)
            hire_manager_user.role_id = hire_manager_role.id
            
            db.session.add(hire_manager_user)
            db.session.commit()
            print(f"  [OK] Created user: {hire_manager_email}")
            print(f"  [OK] Temporary password: {temp_password}")
        
        # 5. Assign user as manager of Hire department
        print("\n5. Assigning Hire Manager to department...")
        if hire_dept.manager_id != hire_manager_user.id:
            hire_dept.manager_id = hire_manager_user.id
            db.session.commit()
            print(f"  [OK] {hire_manager_user.email} is now manager of Hire department")
        else:
            print(f"  [--] {hire_manager_user.email} is already manager of Hire department")
        
        # 6. Create Employee record for the Hire Manager
        print("\n6. Creating employee record...")
        existing_employee = Employee.query.filter_by(user_id=hire_manager_user.id).first()
        if not existing_employee:
            employee = Employee(
                user_id=hire_manager_user.id,
                first_name="Hire",
                last_name="Manager",
                email=hire_manager_email,
                department_id=hire_dept.id,
                position="Hire Manager",
                status="active"
            )
            db.session.add(employee)
            db.session.commit()
            print("  [OK] Created employee record")
        else:
            print("  [--] Employee record already exists")
        
        print("\n" + "=" * 60)
        print("Hire Manager Setup Complete!")
        print("=" * 60)
        print(f"Role: HireManager")
        print(f"Department: Hire (managed by {hire_manager_user.email})")
        print(f"Login email: {hire_manager_email}")
        if temp_password:
            print(f"Temporary password: {temp_password}")
        print("\n[OK] The Hire Manager can now access the Hire department!")
        
        # Print instructions
        print("\nTo assign a different user as Hire Manager:")
        print("1. Go to Admin > Users > Edit User")
        print("2. Assign the HireManager role")
        print("3. Go to Admin > Departments > Edit Hire")
        print("4. Select the user as department manager")

if __name__ == "__main__":
    setup_hire_manager()
