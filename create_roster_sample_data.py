"""Create sample data for Roster Builder - Shifts and Assignments."""
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from sas_management.app import create_app
from sas_management.models import db, Shift, ShiftAssignment, Employee, Department
from datetime import date, timedelta, time

app = create_app()

with app.app_context():
    print("=" * 60)
    print("Creating Sample Roster Data")
    print("=" * 60)
    
    # Get or create departments
    kitchen_dept = Department.query.filter_by(name="Kitchen").first()
    service_dept = Department.query.filter_by(name="Service").first()
    admin_dept = Department.query.filter_by(name="Administration").first()
    
    if not kitchen_dept:
        kitchen_dept = Department(name="Kitchen", description="Kitchen Operations")
        db.session.add(kitchen_dept)
        db.session.flush()
    
    if not service_dept:
        service_dept = Department(name="Service", description="Customer Service")
        db.session.add(service_dept)
        db.session.flush()
    
    if not admin_dept:
        admin_dept = Department(name="Administration", description="Admin Staff")
        db.session.add(admin_dept)
        db.session.flush()
    
    print("\n[1/3] Creating Sample Shifts...")
    
    # Define shifts
    shifts_data = [
        {"name": "Morning Shift", "start_time": time(6, 0), "end_time": time(14, 0), "department": kitchen_dept},
        {"name": "Afternoon Shift", "start_time": time(14, 0), "end_time": time(22, 0), "department": kitchen_dept},
        {"name": "Night Shift", "start_time": time(22, 0), "end_time": time(6, 0), "department": kitchen_dept},
        {"name": "Service Morning", "start_time": time(7, 0), "end_time": time(15, 0), "department": service_dept},
        {"name": "Service Afternoon", "start_time": time(15, 0), "end_time": time(23, 0), "department": service_dept},
        {"name": "Office Hours", "start_time": time(8, 0), "end_time": time(17, 0), "department": admin_dept},
        {"name": "Full Day", "start_time": time(8, 0), "end_time": time(18, 0), "department": None},
    ]
    
    created_shifts = []
    for shift_data in shifts_data:
        existing = Shift.query.filter_by(
            name=shift_data["name"],
            start_time=shift_data["start_time"],
            end_time=shift_data["end_time"]
        ).first()
        
        if not existing:
            shift = Shift(
                name=shift_data["name"],
                start_time=shift_data["start_time"],
                end_time=shift_data["end_time"],
                department_id=shift_data["department"].id if shift_data["department"] else None,
                is_active=True
            )
            db.session.add(shift)
            created_shifts.append(shift)
            print(f"  [OK] Created shift: {shift_data['name']} ({shift_data['start_time'].strftime('%H:%M')} - {shift_data['end_time'].strftime('%H:%M')})")
        else:
            created_shifts.append(existing)
            print(f"  [SKIP] Shift already exists: {shift_data['name']}")
    
    db.session.commit()
    
    print(f"\n[2/3] Getting Active Employees...")
    employees = Employee.query.filter_by(status='active').all()
    
    if not employees:
        print("  [WARN] No active employees found. Please create employees first.")
        print("  You can create employees through: HR -> Employee Management -> Add Employee")
        sys.exit(0)
    
    print(f"  [OK] Found {len(employees)} active employees")
    
    print(f"\n[3/3] Creating Sample Shift Assignments for Current Week...")
    
    # Get current week (Monday to Sunday)
    today = date.today()
    start_date = today - timedelta(days=today.weekday())  # Monday
    end_date = start_date + timedelta(days=6)  # Sunday
    
    assignments_created = 0
    assignments_skipped = 0
    
    # Assign shifts to employees for the week
    for employee in employees:
        # Skip if employee has no department
        if not employee.department_id:
            continue
        
        # Get appropriate shifts for employee's department
        dept_shifts = [s for s in created_shifts if (s.department_id == employee.department_id or s.department_id is None)]
        if not dept_shifts:
            continue
        
        # Assign shifts for the week (Monday, Wednesday, Friday for example)
        for day_offset in [0, 2, 4]:  # Mon, Wed, Fri
            assign_date = start_date + timedelta(days=day_offset)
            
            # Check if assignment already exists
            existing = ShiftAssignment.query.filter_by(
                employee_id=employee.id,
                assignment_date=assign_date
            ).first()
            
            if existing:
                assignments_skipped += 1
                continue
            
            # Select a shift (rotate through available shifts)
            shift = dept_shifts[day_offset % len(dept_shifts)]
            
            assignment = ShiftAssignment(
                shift_id=shift.id,
                employee_id=employee.id,
                assignment_date=assign_date
            )
            db.session.add(assignment)
            assignments_created += 1
    
    db.session.commit()
    
    print(f"\n  [OK] Created {assignments_created} shift assignments")
    print(f"  [SKIP] Skipped {assignments_skipped} (already exist)")
    
    print("\n" + "=" * 60)
    print("SUCCESS!")
    print("=" * 60)
    print(f"[OK] Shifts: {len(created_shifts)} available")
    print(f"[OK] Assignments: {assignments_created} created for week {start_date.strftime('%B %d')} - {end_date.strftime('%B %d, %Y')}")
    print("\nYou can now:")
    print("  1. Go to HR -> Roster Builder")
    print("  2. View the current week's roster")
    print("  3. Assign or modify shifts for employees")
    print("=" * 60)

