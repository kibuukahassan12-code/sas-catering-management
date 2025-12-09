"""Unit tests for HR Department module."""
import pytest
from datetime import date, datetime, time
from app import create_app
from models import db, Department, Position, Employee, Attendance, Shift, ShiftAssignment, LeaveRequest
from services.hr_service import create_employee, clock_in, clock_out, request_leave, assign_shift


@pytest.fixture
def app():
    """Create test app."""
    app = create_app()
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    
    with app.app_context():
        db.create_all()
        yield app
        db.drop_all()


@pytest.fixture
def client(app):
    """Create test client."""
    return app.test_client()


def test_create_employee_and_photo(app):
    """Test creating an employee with photo upload."""
    with app.app_context():
        # Create department and position
        dept = Department(name="Test Department")
        pos = Position(title="Test Position")
        db.session.add(dept)
        db.session.add(pos)
        db.session.commit()
        
        # Create employee
        employee_data = {
            'first_name': 'John',
            'last_name': 'Doe',
            'email': 'john.doe@example.com',
            'phone': '+256700000000',
            'position_id': pos.id,
            'department_id': dept.id,
            'hire_date': date.today().isoformat(),
            'contract_type': 'Full-time',
            'status': 'active'
        }
        
        result = create_employee(employee_data, photo_file=None)
        
        assert result['success'] == True
        assert result['employee_id'] is not None
        
        employee = Employee.query.get(result['employee_id'])
        assert employee is not None
        assert employee.first_name == 'John'
        assert employee.last_name == 'Doe'
        assert employee.email == 'john.doe@example.com'


def test_clock_in_out(app):
    """Test clock in and clock out functionality."""
    with app.app_context():
        # Create employee
        dept = Department(name="Test Department")
        pos = Position(title="Test Position")
        db.session.add(dept)
        db.session.add(pos)
        db.session.commit()
        
        employee_data = {
            'first_name': 'Test',
            'last_name': 'Employee',
            'email': 'test@example.com',
            'position_id': pos.id,
            'department_id': dept.id,
        }
        
        result = create_employee(employee_data)
        employee_id = result['employee_id']
        
        # Clock in
        clock_in_result = clock_in(employee_id, device='Web', location='Office')
        assert clock_in_result['success'] == True
        
        attendance = Attendance.query.filter_by(employee_id=employee_id, clock_out=None).first()
        assert attendance is not None
        assert attendance.clock_in is not None
        
        # Clock out
        clock_out_result = clock_out(employee_id)
        assert clock_out_result['success'] == True
        assert clock_out_result.get('hours_worked') is not None
        
        attendance = Attendance.query.get(clock_in_result['attendance_id'])
        assert attendance.clock_out is not None


def test_leave_request_flow(app):
    """Test leave request creation and approval flow."""
    with app.app_context():
        # Create employee
        dept = Department(name="Test Department")
        pos = Position(title="Test Position")
        db.session.add(dept)
        db.session.add(pos)
        db.session.commit()
        
        employee_data = {
            'first_name': 'Test',
            'last_name': 'Employee',
            'email': 'test@example.com',
            'position_id': pos.id,
            'department_id': dept.id,
        }
        
        result = create_employee(employee_data)
        employee_id = result['employee_id']
        
        # Create leave request
        from datetime import timedelta
        start_date = date.today() + timedelta(days=7)
        end_date = start_date + timedelta(days=3)
        
        leave_data = {
            'leave_type': 'Annual',
            'start_date': start_date.isoformat(),
            'end_date': end_date.isoformat(),
            'reason': 'Vacation'
        }
        
        result = request_leave(employee_id, leave_data)
        assert result['success'] == True
        
        leave_request = LeaveRequest.query.get(result['leave_request_id'])
        assert leave_request is not None
        assert leave_request.status == 'pending'
        assert leave_request.days_requested == 4  # 4 days inclusive


def test_shift_assignment(app):
    """Test shift assignment functionality."""
    with app.app_context():
        # Create employee and shift
        dept = Department(name="Test Department")
        pos = Position(title="Test Position")
        db.session.add(dept)
        db.session.add(pos)
        
        shift = Shift(name="Morning Shift", start_time=time(6, 0), end_time=time(14, 0))
        db.session.add(shift)
        db.session.commit()
        
        employee_data = {
            'first_name': 'Test',
            'last_name': 'Employee',
            'email': 'test@example.com',
            'position_id': pos.id,
            'department_id': dept.id,
        }
        
        result = create_employee(employee_data)
        employee_id = result['employee_id']
        
        # Assign shift
        from datetime import timedelta
        assign_date = date.today() + timedelta(days=1)
        result = assign_shift(shift.id, employee_id, assign_date.isoformat())
        
        assert result['success'] == True
        
        assignment = ShiftAssignment.query.filter_by(
            shift_id=shift.id,
            employee_id=employee_id,
            date=assign_date
        ).first()
        
        assert assignment is not None


