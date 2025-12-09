# HR Department Module - Implementation Summary

## Overview
The HR Department module provides comprehensive employee management, attendance tracking, shift scheduling, leave management, and payroll export functionality.

## Files Created/Modified

### Models (`models.py`)
- `Department` - Department/Division management
- `Position` - Job positions and roles
- `Employee` - Employee records with photos, positions, departments
- `Attendance` - Clock in/out records with approval workflow
- `Shift` - Shift definitions (Morning, Afternoon, Night, Full Day)
- `ShiftAssignment` - Employee shift assignments for specific dates
- `LeaveRequest` - Leave/time-off requests with approval workflow
- `PayrollExport` - Payroll CSV export records

### Service Layer (`services/hr_service.py`)
- `create_employee(data, photo_file=None)` - Create new employee with photo upload
- `get_employee(employee_id)` - Retrieve employee by ID
- `update_employee(employee_id, data, photo_file=None)` - Update employee record
- `list_employees(filters)` - List employees with search/filters
- `clock_in(employee_id, device, location)` - Record clock-in
- `clock_out(employee_id)` - Record clock-out
- `assign_shift(shift_id, employee_id, date_str)` - Assign shift to employee
- `request_leave(employee_id, data)` - Create leave request
- `generate_payroll_export(period_start, period_end, created_by)` - Generate payroll CSV

### Blueprint Routes (`blueprints/hr/__init__.py`)

#### HTML Views:
- `GET /hr/dashboard` - HR dashboard with KPIs
- `GET /hr/employees` - Employee list with search/filters
- `GET /hr/employees/<id>` - Employee profile view
- `GET /hr/roster` - Roster builder (weekly view)
- `GET /hr/leave` - Leave requests queue
- `GET /hr/attendance` - Attendance review and approval
- `GET /hr/payroll` - Payroll export page

#### REST API Endpoints:
- `POST /hr/api/employees` - Create employee (multipart/form-data)
- `PATCH /hr/api/employees/<id>` - Update employee
- `POST /hr/api/employees/<id>/photo` - Upload employee photo
- `POST /hr/api/attendance/clock` - Clock in/out (JSON)
- `POST /hr/api/shifts/assign` - Assign shift (JSON)
- `POST /hr/api/leave` - Request leave (JSON)
- `GET /hr/api/payroll/export?start=YYYY-MM-DD&end=YYYY-MM-DD` - Generate payroll export
- `POST /hr/api/leave/<id>/approve` - Approve leave request
- `POST /hr/api/leave/<id>/reject` - Reject leave request
- `POST /hr/api/attendance/<id>/approve` - Approve attendance record

### Templates (`templates/hr/`)
- `hr_dashboard.html` - Dashboard with KPIs and quick actions
- `employee_list.html` - Employee listing with search/filters
- `employee_profile.html` - Employee profile with attendance, leave, shifts
- `roster_builder.html` - Weekly roster builder
- `leave_queue.html` - Leave request approval interface
- `attendance_review.html` - Attendance review and approval
- `payroll_export.html` - Payroll CSV export generator

### Configuration
- **Blueprint registered** in `app.py`
- **Navigation added** in `routes.py` (HR Department with sub-items)
- **Upload directories** created: `instance/hr_uploads/employee_photos/`, `instance/hr_uploads/docs/`

## Usage Examples

### 1. Create Employee via API
```bash
curl -X POST http://localhost:5000/hr/api/employees \
  -H "Cookie: session=YOUR_SESSION" \
  -F "first_name=John" \
  -F "last_name=Doe" \
  -F "email=john.doe@example.com" \
  -F "phone=+256700000000" \
  -F "position_id=1" \
  -F "department_id=1" \
  -F "contract_type=Full-time" \
  -F "photo=@employee_photo.jpg"
```

### 2. Clock In/Out
```bash
# Clock In
curl -X POST http://localhost:5000/hr/api/attendance/clock \
  -H "Content-Type: application/json" \
  -H "Cookie: session=YOUR_SESSION" \
  -d '{
    "employee_id": 1,
    "action": "in",
    "device": "Web",
    "location": "Office"
  }'

# Clock Out
curl -X POST http://localhost:5000/hr/api/attendance/clock \
  -H "Content-Type: application/json" \
  -H "Cookie: session=YOUR_SESSION" \
  -d '{
    "employee_id": 1,
    "action": "out"
  }'
```

### 3. Request Leave
```bash
curl -X POST http://localhost:5000/hr/api/leave \
  -H "Content-Type: application/json" \
  -H "Cookie: session=YOUR_SESSION" \
  -d '{
    "employee_id": 1,
    "leave_type": "Annual",
    "start_date": "2025-12-01",
    "end_date": "2025-12-05",
    "reason": "Vacation"
  }'
```

### 4. Assign Shift
```bash
curl -X POST http://localhost:5000/hr/api/shifts/assign \
  -H "Content-Type: application/json" \
  -H "Cookie: session=YOUR_SESSION" \
  -d '{
    "shift_id": 1,
    "employee_id": 1,
    "date": "2025-12-01"
  }'
```

### 5. Generate Payroll Export
```bash
curl -X GET "http://localhost:5000/hr/api/payroll/export?start=2025-11-01&end=2025-11-30" \
  -H "Cookie: session=YOUR_SESSION"
```

### 6. Approve Leave Request
```bash
curl -X POST http://localhost:5000/hr/api/leave/1/approve \
  -H "Cookie: session=YOUR_SESSION"
```

## Database Migrations

Run migrations to create HR tables:
```bash
python -m flask db migrate -m "Add HR module tables"
python -m flask db upgrade
```

## Seed Sample Data

Run the seed script to populate initial data:
```bash
python seed_hr_sample_data.py
```

This creates:
- 5 Departments (Production, Kitchen, Bakery, Sales, Administration)
- 6 Positions (Kitchen Staff, Bakery Staff, Production Manager, Sales Manager, Chef, Administrator)
- 4 Shifts (Morning, Afternoon, Night, Full Day)
- 1 Sample Employee (SAS Staff - staff@example.com)

## Testing

Run unit tests:
```bash
python -m pytest tests/test_hr.py -v
```

Test coverage:
- `test_create_employee_and_photo` - Employee creation with photo upload
- `test_clock_in_out` - Attendance clock in/out functionality
- `test_leave_request_flow` - Leave request creation and approval
- `test_shift_assignment` - Shift assignment to employees

## Features

### Employee Management
- ✅ Employee CRUD operations
- ✅ Photo upload and storage
- ✅ Department and position assignment
- ✅ Status management (active, inactive, terminated)
- ✅ Search and filtering

### Attendance Tracking
- ✅ Clock in/out with device and location tracking
- ✅ Hours worked calculation
- ✅ Attendance approval workflow
- ✅ Date range filtering

### Shift Management
- ✅ Shift definitions (time ranges)
- ✅ Weekly roster builder
- ✅ Shift assignment to employees
- ✅ Shift status tracking

### Leave Management
- ✅ Leave request submission
- ✅ Approval/rejection workflow
- ✅ Leave type tracking (Annual, Sick, Personal, Unpaid)
- ✅ Days calculation

### Payroll Export
- ✅ CSV export generation
- ✅ Period-based exports
- ✅ Attendance hours calculation
- ✅ Employee listing with payroll data

## Security Notes

- ✅ Role-based access control (`@role_required` decorator)
- ✅ Admin-only routes for employee management
- ✅ Sensitive fields (bank_account, tax_id) should be encrypted in production
- ✅ Photo uploads validated and sanitized using `secure_filename`

## Integration Points

- **University Module**: Can link employee certifications
- **Payroll Module**: Uses attendance data for payroll calculations
- **Events Module**: Can assign employees to events
- **Notifications**: Ready for email/WhatsApp integration

## Next Steps

1. ✅ Database migrations created
2. ✅ Sample data seeded
3. ⏳ Run comprehensive tests
4. ⏳ Add certificate PDF generation
5. ⏳ Integrate with notification system
6. ⏳ Add employee performance reviews
7. ⏳ Add employee documents management

