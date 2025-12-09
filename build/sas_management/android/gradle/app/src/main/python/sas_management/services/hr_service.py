"""HR Department Service Layer - Employee management, attendance, shifts, leave, payroll."""
import os
import csv
from datetime import datetime, date, time
from flask import current_app
from werkzeug.utils import secure_filename

from models import (
    db, Department, Position, Employee, Attendance, Shift, ShiftAssignment,
    LeaveRequest, PayrollExport, User
)


def create_employee(data, photo_file=None):
    """Create a new employee record."""
    try:
        db.session.begin()
        
        # Validate required fields
        if not data.get('first_name') or not data.get('last_name') or not data.get('email'):
            raise ValueError("First name, last name, and email are required")
        
        # Check if email already exists
        existing = Employee.query.filter_by(email=data['email']).first()
        if existing:
            raise ValueError("Employee with this email already exists")
        
        # Handle photo upload
        photo_url = None
        if photo_file and photo_file.filename:
            upload_folder = os.path.join(current_app.instance_path, "hr_uploads", "employee_photos")
            os.makedirs(upload_folder, exist_ok=True)
            
            filename = secure_filename(photo_file.filename)
            # Add timestamp to avoid collisions
            timestamp = str(int(datetime.utcnow().timestamp()))
            filename = f"{timestamp}_{filename}"
            
            file_path = os.path.join(upload_folder, filename)
            photo_file.save(file_path)
            photo_url = f"hr_uploads/employee_photos/{filename}"
        
        # Parse hire_date if provided
        hire_date = None
        if data.get('hire_date'):
            if isinstance(data['hire_date'], str):
                hire_date = datetime.strptime(data['hire_date'], '%Y-%m-%d').date()
            elif isinstance(data['hire_date'], date):
                hire_date = data['hire_date']
        
        employee = Employee(
            first_name=data['first_name'].strip(),
            last_name=data['last_name'].strip(),
            email=data['email'].strip().lower(),
            phone=data.get('phone', '').strip(),
            photo_url=photo_url,
            position_id=data.get('position_id'),
            department_id=data.get('department_id'),
            hire_date=hire_date,
            contract_type=data.get('contract_type', 'Full-time'),
            status=data.get('status', 'active'),
            bank_account=data.get('bank_account', '').strip(),
            tax_id=data.get('tax_id', '').strip(),
            address=data.get('address', '').strip(),
            emergency_contact=data.get('emergency_contact', '').strip(),
            emergency_phone=data.get('emergency_phone', '').strip()
        )
        
        db.session.add(employee)
        db.session.commit()
        
        return {"success": True, "employee_id": employee.id, "employee": employee}
    except Exception as e:
        db.session.rollback()
        current_app.logger.exception(f"Error creating employee: {e}")
        return {"success": False, "error": str(e)}


def get_employee(employee_id):
    """Get employee by ID."""
    try:
        employee = Employee.query.get(employee_id)
        if not employee:
            return {"success": False, "error": "Employee not found"}
        return {"success": True, "employee": employee}
    except Exception as e:
        current_app.logger.exception(f"Error getting employee: {e}")
        return {"success": False, "error": str(e)}


def update_employee(employee_id, data, photo_file=None):
    """Update employee record."""
    try:
        db.session.begin()
        
        employee = Employee.query.get(employee_id)
        if not employee:
            raise ValueError("Employee not found")
        
        # Update fields
        if 'first_name' in data:
            employee.first_name = data['first_name'].strip()
        if 'last_name' in data:
            employee.last_name = data['last_name'].strip()
        if 'email' in data:
            # Check email uniqueness (excluding current employee)
            existing = Employee.query.filter(Employee.email == data['email'].strip().lower(), Employee.id != employee_id).first()
            if existing:
                raise ValueError("Email already in use by another employee")
            employee.email = data['email'].strip().lower()
        if 'phone' in data:
            employee.phone = data['phone'].strip()
        if 'position_id' in data:
            employee.position_id = data['position_id']
        if 'department_id' in data:
            employee.department_id = data['department_id']
        if 'hire_date' in data and data['hire_date']:
            if isinstance(data['hire_date'], str):
                employee.hire_date = datetime.strptime(data['hire_date'], '%Y-%m-%d').date()
            elif isinstance(data['hire_date'], date):
                employee.hire_date = data['hire_date']
        if 'contract_type' in data:
            employee.contract_type = data['contract_type']
        if 'status' in data:
            employee.status = data['status']
        if 'bank_account' in data:
            employee.bank_account = data['bank_account'].strip()
        if 'tax_id' in data:
            employee.tax_id = data['tax_id'].strip()
        if 'address' in data:
            employee.address = data['address'].strip()
        if 'emergency_contact' in data:
            employee.emergency_contact = data['emergency_contact'].strip()
        if 'emergency_phone' in data:
            employee.emergency_phone = data['emergency_phone'].strip()
        
        # Handle photo upload
        if photo_file and photo_file.filename:
            upload_folder = os.path.join(current_app.instance_path, "hr_uploads", "employee_photos")
            os.makedirs(upload_folder, exist_ok=True)
            
            # Delete old photo if exists
            if employee.photo_url:
                old_path = os.path.join(current_app.instance_path, employee.photo_url)
                if os.path.exists(old_path):
                    try:
                        os.remove(old_path)
                    except:
                        pass
            
            filename = secure_filename(photo_file.filename)
            timestamp = str(int(datetime.utcnow().timestamp()))
            filename = f"{timestamp}_{filename}"
            
            file_path = os.path.join(upload_folder, filename)
            photo_file.save(file_path)
            employee.photo_url = f"hr_uploads/employee_photos/{filename}"
        
        employee.updated_at = datetime.utcnow()
        db.session.commit()
        
        return {"success": True, "employee": employee}
    except Exception as e:
        db.session.rollback()
        current_app.logger.exception(f"Error updating employee: {e}")
        return {"success": False, "error": str(e)}


def list_employees(filters=None):
    """List employees with optional filters."""
    try:
        query = Employee.query
        
        if filters:
            if filters.get('department_id'):
                query = query.filter(Employee.department_id == filters['department_id'])
            if filters.get('position_id'):
                query = query.filter(Employee.position_id == filters['position_id'])
            if filters.get('status'):
                query = query.filter(Employee.status == filters['status'])
            if filters.get('search'):
                search_term = f"%{filters['search']}%"
                query = query.filter(
                    db.or_(
                        Employee.first_name.ilike(search_term),
                        Employee.last_name.ilike(search_term),
                        Employee.email.ilike(search_term)
                    )
                )
        
        employees = query.order_by(Employee.last_name.asc(), Employee.first_name.asc()).all()
        return {"success": True, "employees": employees}
    except Exception as e:
        current_app.logger.exception(f"Error listing employees: {e}")
        return {"success": False, "error": str(e), "employees": []}


def clock_in(employee_id, device=None, location=None):
    """Record employee clock-in."""
    try:
        db.session.begin()
        
        employee = Employee.query.get(employee_id)
        if not employee:
            raise ValueError("Employee not found")
        
        # Check if there's an open attendance record (clocked in but not clocked out)
        open_attendance = Attendance.query.filter_by(
            employee_id=employee_id,
            clock_out=None
        ).first()
        
        if open_attendance:
            raise ValueError("Employee already clocked in. Please clock out first.")
        
        attendance = Attendance(
            employee_id=employee_id,
            clock_in=datetime.utcnow(),
            device=device or 'Web',
            location=location or 'Office'
        )
        
        db.session.add(attendance)
        db.session.commit()
        
        return {"success": True, "attendance_id": attendance.id, "attendance": attendance}
    except Exception as e:
        db.session.rollback()
        current_app.logger.exception(f"Error clocking in: {e}")
        return {"success": False, "error": str(e)}


def clock_out(employee_id):
    """Record employee clock-out."""
    try:
        db.session.begin()
        
        employee = Employee.query.get(employee_id)
        if not employee:
            raise ValueError("Employee not found")
        
        # Find the most recent open attendance record
        attendance = Attendance.query.filter_by(
            employee_id=employee_id,
            clock_out=None
        ).order_by(Attendance.clock_in.desc()).first()
        
        if not attendance:
            raise ValueError("No active clock-in found. Please clock in first.")
        
        attendance.clock_out = datetime.utcnow()
        db.session.commit()
        
        return {"success": True, "attendance": attendance, "hours_worked": attendance.hours_worked}
    except Exception as e:
        db.session.rollback()
        current_app.logger.exception(f"Error clocking out: {e}")
        return {"success": False, "error": str(e)}


def assign_shift(shift_id, employee_id, date_str):
    """Assign shift to employee for a specific date."""
    try:
        db.session.begin()
        
        shift = Shift.query.get(shift_id)
        if not shift:
            raise ValueError("Shift not found")
        
        employee = Employee.query.get(employee_id)
        if not employee:
            raise ValueError("Employee not found")
        
        # Parse date
        if isinstance(date_str, str):
            assign_date = datetime.strptime(date_str, '%Y-%m-%d').date()
        elif isinstance(date_str, date):
            assign_date = date_str
        else:
            raise ValueError("Invalid date format")
        
        # Check if assignment already exists
        existing = ShiftAssignment.query.filter_by(
            shift_id=shift_id,
            employee_id=employee_id,
            date=assign_date
        ).first()
        
        if existing:
            raise ValueError("Shift assignment already exists for this date")
        
        assignment = ShiftAssignment(
            shift_id=shift_id,
            employee_id=employee_id,
            date=assign_date
        )
        
        db.session.add(assignment)
        db.session.commit()
        
        return {"success": True, "assignment_id": assignment.id, "assignment": assignment}
    except Exception as e:
        db.session.rollback()
        current_app.logger.exception(f"Error assigning shift: {e}")
        return {"success": False, "error": str(e)}


def request_leave(employee_id, data):
    """Create leave request."""
    try:
        db.session.begin()
        
        employee = Employee.query.get(employee_id)
        if not employee:
            raise ValueError("Employee not found")
        
        # Parse dates
        start_date = datetime.strptime(data['start_date'], '%Y-%m-%d').date() if isinstance(data['start_date'], str) else data['start_date']
        end_date = datetime.strptime(data['end_date'], '%Y-%m-%d').date() if isinstance(data['end_date'], str) else data['end_date']
        
        if end_date < start_date:
            raise ValueError("End date cannot be before start date")
        
        leave_request = LeaveRequest(
            employee_id=employee_id,
            leave_type=data.get('leave_type', 'Annual'),
            start_date=start_date,
            end_date=end_date,
            reason=data.get('reason', '').strip()
        )
        
        db.session.add(leave_request)
        db.session.commit()
        
        return {"success": True, "leave_request_id": leave_request.id, "leave_request": leave_request}
    except Exception as e:
        db.session.rollback()
        current_app.logger.exception(f"Error creating leave request: {e}")
        return {"success": False, "error": str(e)}


def generate_payroll_export(period_start, period_end, created_by=None):
    """Generate payroll CSV export."""
    try:
        db.session.begin()
        
        # Parse dates
        if isinstance(period_start, str):
            period_start = datetime.strptime(period_start, '%Y-%m-%d').date()
        if isinstance(period_end, str):
            period_end = datetime.strptime(period_end, '%Y-%m-%d').date()
        
        # Get active employees
        employees = Employee.query.filter_by(status='active').all()
        
        # Create export record
        export = PayrollExport(
            period_start=period_start,
            period_end=period_end,
            employee_count=len(employees),
            created_by=created_by,
            status='pending'
        )
        db.session.add(export)
        db.session.flush()
        
        # Generate CSV file
        upload_folder = os.path.join(current_app.instance_path, "hr_uploads", "docs")
        os.makedirs(upload_folder, exist_ok=True)
        
        filename = f"payroll_export_{period_start}_{period_end}_{export.id}.csv"
        file_path = os.path.join(upload_folder, filename)
        
        total_amount = 0
        
        with open(file_path, 'w', newline='', encoding='utf-8') as csvfile:
            fieldnames = ['Employee ID', 'Name', 'Email', 'Position', 'Department', 'Days Worked', 'Hours Worked', 'Basic Salary', 'Allowances', 'Deductions', 'Net Pay']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            
            writer.writeheader()
            
            for employee in employees:
                # Calculate attendance for period
                attendances = Attendance.query.filter(
                    Attendance.employee_id == employee.id,
                    db.func.date(Attendance.clock_in) >= period_start,
                    db.func.date(Attendance.clock_in) <= period_end,
                    Attendance.approved == True
                ).all()
                
                days_worked = len(set(a.clock_in.date() for a in attendances if a.clock_in))
                hours_worked = sum([a.hours_worked or 0 for a in attendances])
                
                # Placeholder calculations (would integrate with actual payroll system)
                basic_salary = 500000  # Placeholder
                allowances = 100000
                deductions = 50000
                net_pay = basic_salary + allowances - deductions
                total_amount += net_pay
                
                writer.writerow({
                    'Employee ID': employee.id,
                    'Name': employee.full_name,
                    'Email': employee.email,
                    'Position': employee.position.title if employee.position else 'N/A',
                    'Department': employee.department.name if employee.department else 'N/A',
                    'Days Worked': days_worked,
                    'Hours Worked': round(hours_worked, 2),
                    'Basic Salary': basic_salary,
                    'Allowances': allowances,
                    'Deductions': deductions,
                    'Net Pay': net_pay
                })
        
        # Update export record
        export.file_path = f"hr_uploads/docs/{filename}"
        export.total_amount = total_amount
        export.status = 'completed'
        
        db.session.commit()
        
        return {"success": True, "export_id": export.id, "file_path": export.file_path, "export": export}
    except Exception as e:
        db.session.rollback()
        current_app.logger.exception(f"Error generating payroll export: {e}")
        return {"success": False, "error": str(e)}


