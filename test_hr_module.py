"""Quick test script to verify HR module functionality."""
from app import create_app
from models import db, Department, Position, Employee, Shift, Attendance, LeaveRequest
from sqlalchemy import inspect

def test_hr_module():
    """Test HR module setup."""
    print("\n" + "="*60)
    print("HR MODULE VERIFICATION")
    print("="*60)
    
    app = create_app()
    
    with app.app_context():
        # Check database tables
        print("\n1. Checking Database Tables...")
        inspector = inspect(db.engine)
        tables = inspector.get_table_names()
        hr_tables = ['department', 'position', 'employee', 'attendance', 
                     'shift', 'shift_assignment', 'leave_request', 'payroll_export']
        
        found_tables = []
        missing_tables = []
        for table in hr_tables:
            if table in tables:
                found_tables.append(table)
                print(f"   ✓ {table}")
            else:
                missing_tables.append(table)
                print(f"   ✗ {table} (missing)")
        
        if missing_tables:
            print(f"\n   ⚠️  Missing tables: {missing_tables}")
            print("   Running db.create_all()...")
            db.create_all()
        else:
            print(f"\n   ✅ All {len(hr_tables)} HR tables exist")
        
        # Check data
        print("\n2. Checking Sample Data...")
        depts = Department.query.count()
        positions = Position.query.count()
        employees = Employee.query.count()
        shifts = Shift.query.count()
        
        print(f"   Departments: {depts}")
        print(f"   Positions: {positions}")
        print(f"   Employees: {employees}")
        print(f"   Shifts: {shifts}")
        
        if employees > 0:
            sample_employee = Employee.query.first()
            print(f"\n   ✓ Sample employee found: {sample_employee.full_name}")
            print(f"      Email: {sample_employee.email}")
            print(f"      Department: {sample_employee.department.name if sample_employee.department else 'N/A'}")
            print(f"      Position: {sample_employee.position.title if sample_employee.position else 'N/A'}")
        
        # Check routes
        print("\n3. Checking Routes...")
        hr_routes = [str(r) for r in app.url_map.iter_rules() if 'hr' in r.endpoint]
        print(f"   ✅ {len(hr_routes)} HR routes registered")
        
        # Check blueprint
        print("\n4. Checking Blueprint...")
        from blueprints.hr import hr_bp
        print(f"   ✅ HR blueprint registered: {hr_bp.name}")
        print(f"   ✅ Blueprint URL prefix: {hr_bp.url_prefix}")
        
        # Check services
        print("\n5. Checking Services...")
        try:
            from services.hr_service import (
                create_employee, get_employee, update_employee, list_employees,
                clock_in, clock_out, assign_shift, request_leave, generate_payroll_export
            )
            print("   ✅ All HR service functions imported successfully")
        except Exception as e:
            print(f"   ✗ Error importing services: {e}")
        
        # Check upload directories
        print("\n6. Checking Upload Directories...")
        import os
        photo_dir = os.path.join(app.instance_path, "hr_uploads", "employee_photos")
        docs_dir = os.path.join(app.instance_path, "hr_uploads", "docs")
        
        if os.path.exists(photo_dir):
            print(f"   ✅ Employee photos directory: {photo_dir}")
        else:
            print(f"   ✗ Employee photos directory missing")
        
        if os.path.exists(docs_dir):
            print(f"   ✅ Docs directory: {docs_dir}")
        else:
            print(f"   ✗ Docs directory missing")
        
        # Check templates
        print("\n7. Checking Templates...")
        import os
        template_dir = os.path.join("templates", "hr")
        if os.path.exists(template_dir):
            templates = [f for f in os.listdir(template_dir) if f.endswith('.html')]
            print(f"   ✅ {len(templates)} templates found:")
            for t in templates:
                print(f"      - {t}")
        else:
            print(f"   ✗ Templates directory missing")
        
        print("\n" + "="*60)
        print("VERIFICATION COMPLETE")
        print("="*60 + "\n")

if __name__ == "__main__":
    test_hr_module()

