#!/usr/bin/env python3
"""
Add sample attendance data to the system
"""

import sys
import os
from datetime import datetime, date, timedelta
from decimal import Decimal
import random

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app, db
from models import (
    Employee,
    Attendance,
    Department,
    Position,
    User,
    UserRole,
)

def add_attendance_sample_data():
    """Add comprehensive sample attendance data."""
    app = create_app()
    
    with app.app_context():
        print("=" * 60)
        print("ADDING ATTENDANCE SAMPLE DATA")
        print("=" * 60)
        print()
        
        # Get employees
        employees = Employee.query.filter_by(is_active=True).all()
        if not employees:
            print("❌ No active employees found. Creating sample employees first...")
            
            # Create a sample department if none exists
            dept = Department.query.first()
            if not dept:
                dept = Department(name="Operations", description="Operations Department")
                db.session.add(dept)
                db.session.flush()
            
            # Create sample employees
            sample_employees = [
                {"first_name": "John", "last_name": "Doe", "email": "john.doe@example.com", "phone": "0700123456"},
                {"first_name": "Jane", "last_name": "Smith", "email": "jane.smith@example.com", "phone": "0700123457"},
                {"first_name": "Michael", "last_name": "Johnson", "email": "michael.j@example.com", "phone": "0700123458"},
                {"first_name": "Sarah", "last_name": "Williams", "email": "sarah.w@example.com", "phone": "0700123459"},
                {"first_name": "David", "last_name": "Brown", "email": "david.b@example.com", "phone": "0700123460"},
            ]
            
            for emp_data in sample_employees:
                employee = Employee(
                    first_name=emp_data["first_name"],
                    last_name=emp_data["last_name"],
                    email=emp_data["email"],
                    phone=emp_data["phone"],
                    department_id=dept.id,
                    is_active=True,
                    status="active",
                )
                db.session.add(employee)
                print(f"   ✓ Created employee: {emp_data['first_name']} {emp_data['last_name']}")
            
            db.session.commit()
            employees = Employee.query.filter_by(is_active=True).all()
        
        print(f"Found {len(employees)} employees")
        print()
        
        # Create attendance records for the past 30 days
        print("Creating attendance records for the past 30 days...")
        today = date.today()
        records_created = 0
        
        for day_offset in range(30):
            record_date = today - timedelta(days=day_offset)
            
            # Skip weekends (Saturday=5, Sunday=6)
            if record_date.weekday() >= 5:
                continue
            
            for employee in employees:
                # Check if record already exists
                existing = Attendance.query.filter_by(
                    employee_id=employee.id,
                    date=record_date
                ).first()
                
                if existing:
                    continue
                
                # Random clock in time between 7:00 AM and 9:00 AM
                clock_in_hour = random.randint(7, 9)
                clock_in_minute = random.randint(0, 59)
                clock_in = datetime.combine(record_date, datetime.min.time().replace(hour=clock_in_hour, minute=clock_in_minute))
                
                # Random clock out time between 4:00 PM and 6:00 PM
                clock_out_hour = random.randint(16, 18)
                clock_out_minute = random.randint(0, 59)
                clock_out = datetime.combine(record_date, datetime.min.time().replace(hour=clock_out_hour, minute=clock_out_minute))
                
                # Calculate hours worked
                time_diff = clock_out - clock_in
                hours_worked = Decimal(str(time_diff.total_seconds() / 3600))
                
                # Determine status
                if clock_in.hour > 8 or (clock_in.hour == 8 and clock_in.minute > 30):
                    status = "Late"
                else:
                    status = "Present"
                
                attendance = Attendance(
                    employee_id=employee.id,
                    date=record_date,
                    clock_in=clock_in,
                    clock_out=clock_out,
                    hours_worked=hours_worked,
                    status=status,
                )
                db.session.add(attendance)
                records_created += 1
        
        try:
            db.session.commit()
            print(f"\n✅ Created {records_created} attendance records")
            print("\n" + "=" * 60)
            print("✅ ATTENDANCE SAMPLE DATA ADDED SUCCESSFULLY")
            print("=" * 60)
            print(f"\nCreated attendance records for {len(employees)} employees")
            print("Records span the past 30 days (excluding weekends)")
            print()
            return True
        except Exception as e:
            db.session.rollback()
            print(f"\n❌ Error: {e}")
            import traceback
            traceback.print_exc()
            return False

if __name__ == "__main__":
    success = add_attendance_sample_data()
    sys.exit(0 if success else 1)

