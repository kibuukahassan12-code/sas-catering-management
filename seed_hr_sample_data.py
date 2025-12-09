"""Seed HR Department sample data."""
from app import create_app
from models import db, Department, Position, Employee, Shift
from datetime import date, datetime, time
import os
import shutil

def seed_hr_data():
    """Seed HR sample data."""
    app = create_app()
    
    with app.app_context():
        try:
            # Create Departments
            departments_data = [
                {"name": "Production", "manager_id": None},
                {"name": "Kitchen", "manager_id": None},
                {"name": "Bakery", "manager_id": None},
                {"name": "Sales", "manager_id": None},
                {"name": "Administration", "manager_id": None},
            ]
            
            for dept_data in departments_data:
                existing = Department.query.filter_by(name=dept_data["name"]).first()
                if not existing:
                    dept = Department(**dept_data)
                    db.session.add(dept)
            
            db.session.commit()
            
            # Create Positions
            positions_data = [
                {"title": "Kitchen Staff", "grade": "Entry"},
                {"title": "Bakery Staff", "grade": "Entry"},
                {"title": "Production Manager", "grade": "Manager"},
                {"title": "Sales Manager", "grade": "Manager"},
                {"title": "Chef", "grade": "Senior"},
                {"title": "Administrator", "grade": "Mid"},
            ]
            
            for pos_data in positions_data:
                existing = Position.query.filter_by(title=pos_data["title"]).first()
                if not existing:
                    pos = Position(**pos_data)
                    db.session.add(pos)
            
            db.session.commit()
            
            # Create Shifts
            shifts_data = [
                {"name": "Morning Shift", "start_time": time(6, 0), "end_time": time(14, 0)},
                {"name": "Afternoon Shift", "start_time": time(14, 0), "end_time": time(22, 0)},
                {"name": "Night Shift", "start_time": time(22, 0), "end_time": time(6, 0)},
                {"name": "Full Day", "start_time": time(8, 0), "end_time": time(17, 0)},
            ]
            
            for shift_data in shifts_data:
                existing = Shift.query.filter_by(name=shift_data["name"]).first()
                if not existing:
                    shift = Shift(**shift_data)
                    db.session.add(shift)
            
            db.session.commit()
            
            # Create Sample Employee
            production_dept = Department.query.filter_by(name="Production").first()
            kitchen_position = Position.query.filter_by(title="Kitchen Staff").first()
            
            if production_dept and kitchen_position:
                existing_employee = Employee.query.filter_by(email="staff@example.com").first()
                if not existing_employee:
                    # Copy sample photo
                    sample_photo_source = "/mnt/data/drwa.JPG"
                    upload_folder = os.path.join(app.instance_path, "hr_uploads", "employee_photos")
                    os.makedirs(upload_folder, exist_ok=True)
                    sample_photo_dest = os.path.join(upload_folder, "sample_photo.jpg")
                    
                    # Try to copy sample image if it exists
                    photo_url = None
                    if os.path.exists(sample_photo_source):
                        try:
                            shutil.copy2(sample_photo_source, sample_photo_dest)
                            photo_url = "hr_uploads/employee_photos/sample_photo.jpg"
                        except Exception as e:
                            print(f"Warning: Could not copy sample photo: {e}")
                            # Create a placeholder
                            photo_url = "hr_uploads/employee_photos/sample_photo.jpg"
                    
                    employee = Employee(
                        first_name="SAS",
                        last_name="Staff",
                        email="staff@example.com",
                        phone="+256700000000",
                        photo_url=photo_url,
                        position_id=kitchen_position.id,
                        department_id=production_dept.id,
                        hire_date=date.today(),
                        contract_type="Full-time",
                        status="active"
                    )
                    
                    db.session.add(employee)
                    db.session.commit()
                    
                    print(f"✓ Created sample employee: {employee.full_name}")
            
            print("✓ HR sample data seeded successfully")
            
        except Exception as e:
            db.session.rollback()
            print(f"✗ Error seeding HR data: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    seed_hr_data()


