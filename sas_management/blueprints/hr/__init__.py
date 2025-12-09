"""HR Department Blueprint - Employee management, attendance, shifts, leave, payroll."""
import os
from datetime import datetime
from flask import Blueprint, flash, redirect, render_template, request, url_for, jsonify, send_file, send_from_directory, current_app
from flask_login import login_required

from models import (
    db, Department, Position, Employee, Attendance, Shift, ShiftAssignment,
    LeaveRequest, PayrollExport, User, UserRole
)
from services.hr_service import (
    create_employee, get_employee, update_employee, list_employees,
    clock_in, clock_out, assign_shift, request_leave, generate_payroll_export
)
from utils import paginate_query, role_required

hr_bp = Blueprint("hr", __name__, url_prefix="/hr")


# ============================
# HTML VIEWS
# ============================

@hr_bp.route("/dashboard")
@login_required
def dashboard():
    """HR Dashboard with KPIs."""
    try:
        from sqlalchemy import func
        from datetime import date, timedelta
        
        # KPIs
        total_employees = Employee.query.filter_by(status='active').count()
        total_departments = Department.query.count()
        pending_leave_requests = LeaveRequest.query.filter_by(status='pending').count()
        
        # Today's attendance
        today = date.today()
        today_attendances = Attendance.query.filter(
            db.func.date(Attendance.clock_in) == today
        ).count()
        
        # Clocked in now (no clock out today)
        clocked_in_now = Attendance.query.filter(
            db.func.date(Attendance.clock_in) == today,
            Attendance.clock_out == None
        ).count()
        
        # Recent activity
        recent_employees = Employee.query.order_by(Employee.created_at.desc()).limit(5).all()
        recent_leave_requests = LeaveRequest.query.filter_by(status='pending').order_by(LeaveRequest.applied_at.desc()).limit(5).all()
        
        return render_template("hr/hr_dashboard.html",
            total_employees=total_employees,
            total_departments=total_departments,
            pending_leave_requests=pending_leave_requests,
            today_attendances=today_attendances,
            clocked_in_now=clocked_in_now,
            recent_employees=recent_employees,
            recent_leave_requests=recent_leave_requests
        )
    except Exception as e:
        current_app.logger.exception(f"Error loading HR dashboard: {e}")
        return render_template("hr/hr_dashboard.html",
            total_employees=0,
            total_departments=0,
            pending_leave_requests=0,
            today_attendances=0,
            clocked_in_now=0,
            recent_employees=[],
            recent_leave_requests=[]
        )


@hr_bp.route("/employees")
@login_required
def employee_list():
    """List all employees with search and filters."""
    try:
        search = request.args.get('search', '').strip()
        department_id = request.args.get('department_id', type=int)
        status = request.args.get('status', 'active')
        
        filters = {}
        if search:
            filters['search'] = search
        if department_id:
            filters['department_id'] = department_id
        if status:
            filters['status'] = status
        
        result = list_employees(filters)
        employees = result.get('employees', [])
        
        departments = Department.query.order_by(Department.name.asc()).all()
        positions = Position.query.order_by(Position.title.asc()).all()
        
        return render_template("hr/employee_list.html",
            employees=employees,
            departments=departments,
            positions=positions,
            search=search,
            department_id=department_id,
            status=status
        )
    except Exception as e:
        current_app.logger.exception(f"Error loading employee list: {e}")
        return render_template("hr/employee_list.html",
            employees=[],
            departments=[],
            positions=[],
            search="",
            department_id=None,
            status="active"
        )


@hr_bp.route("/employees/<int:employee_id>")
@login_required
def employee_profile(employee_id):
    """View employee profile."""
    try:
        result = get_employee(employee_id)
        if not result['success']:
            flash(result.get('error', 'Employee not found'), "danger")
            return redirect(url_for("hr.employee_list"))
        
        employee = result['employee']
        
        # Get related data
        attendances = Attendance.query.filter_by(employee_id=employee_id).order_by(Attendance.clock_in.desc()).limit(10).all()
        leave_requests = LeaveRequest.query.filter_by(employee_id=employee_id).order_by(LeaveRequest.applied_at.desc()).limit(10).all()
        shift_assignments = ShiftAssignment.query.filter_by(employee_id=employee_id).order_by(ShiftAssignment.date.desc()).limit(10).all()
        
        departments = Department.query.order_by(Department.name.asc()).all()
        positions = Position.query.order_by(Position.title.asc()).all()
        
        return render_template("hr/employee_profile.html",
            employee=employee,
            attendances=attendances,
            leave_requests=leave_requests,
            shift_assignments=shift_assignments,
            departments=departments,
            positions=positions
        )
    except Exception as e:
        current_app.logger.exception(f"Error loading employee profile: {e}")
        return redirect(url_for("hr.employee_list"))


@hr_bp.route("/roster")
@login_required
def roster_builder():
    """Roster builder page."""
    try:
        shifts = Shift.query.order_by(Shift.name.asc()).all()
        employees = Employee.query.filter_by(status='active').order_by(Employee.last_name.asc()).all()
        
        # Get date range (default: current week)
        from datetime import date, timedelta
        today = date.today()
        start_date = today - timedelta(days=today.weekday())  # Monday of current week
        end_date = start_date + timedelta(days=6)  # Sunday
        
        # Get assignments for this week
        assignments = ShiftAssignment.query.filter(
            ShiftAssignment.date >= start_date,
            ShiftAssignment.date <= end_date
        ).order_by(ShiftAssignment.date.asc()).all()
        
        # Calculate date range for template
        from datetime import timedelta
        date_range = []
        if start_date and end_date:
            current = start_date
            while current <= end_date:
                date_range.append(current)
                current += timedelta(days=1)
        
        return render_template("hr/roster_builder.html",
            shifts=shifts,
            employees=employees,
            assignments=assignments,
            start_date=start_date,
            end_date=end_date,
            date_range=date_range,
            timedelta=timedelta
        )
    except Exception as e:
        current_app.logger.exception(f"Error loading roster: {e}")
        return render_template("hr/roster_builder.html",
            shifts=[],
            employees=[],
            assignments=[],
            start_date=None,
            end_date=None
        )


@hr_bp.route("/leave")
@login_required
def leave_queue():
    """Leave requests queue for approval."""
    try:
        status = request.args.get('status', 'pending')
        
        query = LeaveRequest.query
        if status != 'all':
            query = query.filter_by(status=status)
        
        leave_requests = query.order_by(LeaveRequest.applied_at.desc()).all()
        employees = Employee.query.filter_by(status='active').all()
        
        return render_template("hr/leave_queue.html",
            leave_requests=leave_requests,
            employees=employees,
            status=status
        )
    except Exception as e:
        current_app.logger.exception(f"Error loading leave queue: {e}")
        return render_template("hr/leave_queue.html",
            leave_requests=[],
            employees=[],
            status="pending"
        )


@hr_bp.route("/attendance")
@login_required
def attendance_review():
    """Attendance review and approval."""
    try:
        from datetime import date, timedelta
        
        # Default to current week
        today = date.today()
        start_date = today - timedelta(days=today.weekday())
        end_date = start_date + timedelta(days=6)
        
        # Get date range from request
        start_str = request.args.get('start_date', start_date.isoformat())
        end_str = request.args.get('end_date', end_date.isoformat())
        
        start_date = datetime.strptime(start_str, '%Y-%m-%d').date()
        end_date = datetime.strptime(end_str, '%Y-%m-%d').date()
        
        # Get attendances in date range - use date field if available, otherwise clock_in date
        attendances = Attendance.query.filter(
            Attendance.date >= start_date,
            Attendance.date <= end_date
        ).order_by(Attendance.date.desc(), Attendance.clock_in.desc()).all()
        
        # Also try to get by clock_in date for records that might not have date field set
        if not attendances:
            attendances = Attendance.query.filter(
                db.func.date(Attendance.clock_in) >= start_date,
                db.func.date(Attendance.clock_in) <= end_date
            ).order_by(Attendance.clock_in.desc()).all()
        
        employees = Employee.query.filter_by(status='active').all()
        
        # Calculate summary statistics
        total_records = len(attendances)
        present_count = sum(1 for a in attendances if a.status == 'Present')
        late_count = sum(1 for a in attendances if a.status == 'Late')
        absent_count = sum(1 for a in attendances if a.status == 'Absent')
        total_hours = sum(float(a.hours_worked or 0) for a in attendances)
        
        return render_template("hr/attendance_review.html",
            attendances=attendances,
            employees=employees,
            start_date=start_date,
            end_date=end_date,
            total_records=total_records,
            present_count=present_count,
            late_count=late_count,
            absent_count=absent_count,
            total_hours=total_hours,
        )
    except Exception as e:
        current_app.logger.exception(f"Error loading attendance review: {e}")
        return render_template("hr/attendance_review.html",
            attendances=[],
            employees=[],
            start_date=None,
            end_date=None,
            total_records=0,
            present_count=0,
            late_count=0,
            absent_count=0,
            total_hours=0.0,
        )


@hr_bp.route("/payroll")
@login_required
@role_required(UserRole.Admin, UserRole.SalesManager)
def payroll_export():
    """Payroll export page."""
    try:
        # Get recent exports
        recent_exports = PayrollExport.query.order_by(PayrollExport.created_at.desc()).limit(10).all()
        
        return render_template("hr/payroll_export.html",
            recent_exports=recent_exports
        )
    except Exception as e:
        current_app.logger.exception(f"Error loading payroll export: {e}")
        return render_template("hr/payroll_export.html",
            recent_exports=[]
        )


# ============================
# REST API ENDPOINTS
# ============================

@hr_bp.route("/api/employees", methods=["POST"])
@login_required
@role_required(UserRole.Admin)
def api_create_employee():
    """API: Create new employee."""
    try:
        data = request.form.to_dict()
        
        # Handle photo upload
        photo_file = request.files.get('photo')
        
        result = create_employee(data, photo_file)
        
        if result['success']:
            return jsonify({"success": True, "employee_id": result['employee_id'], "message": "Employee created successfully"}), 201
        else:
            return jsonify({"success": False, "error": result.get('error', 'Failed to create employee')}), 400
    except Exception as e:
        current_app.logger.exception(f"Error creating employee via API: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


@hr_bp.route("/api/employees/<int:employee_id>", methods=["PATCH", "PUT"])
@login_required
@role_required(UserRole.Admin)
def api_update_employee(employee_id):
    """API: Update employee."""
    try:
        if request.is_json:
            data = request.get_json()
            photo_file = None
        else:
            data = request.form.to_dict()
            photo_file = request.files.get('photo')
        
        result = update_employee(employee_id, data, photo_file)
        
        if result['success']:
            return jsonify({"success": True, "message": "Employee updated successfully"}), 200
        else:
            return jsonify({"success": False, "error": result.get('error', 'Failed to update employee')}), 400
    except Exception as e:
        current_app.logger.exception(f"Error updating employee via API: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


@hr_bp.route("/api/employees/<int:employee_id>/photo", methods=["POST"])
@login_required
@role_required(UserRole.Admin)
def api_upload_employee_photo(employee_id):
    """API: Upload employee photo."""
    try:
        if 'photo' not in request.files:
            return jsonify({"success": False, "error": "No photo file provided"}), 400
        
        photo_file = request.files['photo']
        if not photo_file.filename:
            return jsonify({"success": False, "error": "No file selected"}), 400
        
        result = update_employee(employee_id, {}, photo_file)
        
        if result['success']:
            return jsonify({"success": True, "photo_url": result['employee'].photo_url, "message": "Photo uploaded successfully"}), 200
        else:
            return jsonify({"success": False, "error": result.get('error', 'Failed to upload photo')}), 400
    except Exception as e:
        current_app.logger.exception(f"Error uploading photo via API: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


@hr_bp.route("/api/attendance/clock", methods=["POST"])
@login_required
def api_clock_attendance():
    """API: Clock in or out."""
    try:
        if not request.is_json:
            return jsonify({"success": False, "error": "Request must be JSON"}), 400
        
        data = request.get_json()
        employee_id = data.get('employee_id')
        action = data.get('action', 'in')  # 'in' or 'out'
        device = data.get('device', 'Web')
        location = data.get('location', 'Office')
        
        if not employee_id:
            return jsonify({"success": False, "error": "employee_id is required"}), 400
        
        if action == 'in':
            result = clock_in(employee_id, device, location)
        elif action == 'out':
            result = clock_out(employee_id)
        else:
            return jsonify({"success": False, "error": "action must be 'in' or 'out'"}), 400
        
        if result['success']:
            return jsonify({"success": True, "attendance": {
                "id": result['attendance'].id,
                "clock_in": result['attendance'].clock_in.isoformat() if result['attendance'].clock_in else None,
                "clock_out": result['attendance'].clock_out.isoformat() if result['attendance'].clock_out else None,
                "hours_worked": result.get('hours_worked')
            }}), 200
        else:
            return jsonify({"success": False, "error": result.get('error', 'Failed to clock attendance')}), 400
    except Exception as e:
        current_app.logger.exception(f"Error clocking attendance via API: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


@hr_bp.route("/api/shifts/assign", methods=["POST"])
@login_required
@role_required(UserRole.Admin)
def api_assign_shift():
    """API: Assign shift to employee."""
    try:
        if not request.is_json:
            return jsonify({"success": False, "error": "Request must be JSON"}), 400
        
        data = request.get_json()
        shift_id = data.get('shift_id')
        employee_id = data.get('employee_id')
        date_str = data.get('date')
        
        if not all([shift_id, employee_id, date_str]):
            return jsonify({"success": False, "error": "shift_id, employee_id, and date are required"}), 400
        
        result = assign_shift(shift_id, employee_id, date_str)
        
        if result['success']:
            return jsonify({"success": True, "assignment_id": result['assignment_id'], "message": "Shift assigned successfully"}), 200
        else:
            return jsonify({"success": False, "error": result.get('error', 'Failed to assign shift')}), 400
    except Exception as e:
        current_app.logger.exception(f"Error assigning shift via API: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


@hr_bp.route("/api/leave", methods=["POST"])
@login_required
def api_request_leave():
    """API: Create leave request."""
    try:
        if not request.is_json:
            return jsonify({"success": False, "error": "Request must be JSON"}), 400
        
        data = request.get_json()
        employee_id = data.get('employee_id', current_user.id)
        leave_type = data.get('leave_type', 'Annual')
        start_date = data.get('start_date')
        end_date = data.get('end_date')
        reason = data.get('reason', '')
        
        if not all([start_date, end_date]):
            return jsonify({"success": False, "error": "start_date and end_date are required"}), 400
        
        leave_data = {
            'leave_type': leave_type,
            'start_date': start_date,
            'end_date': end_date,
            'reason': reason
        }
        
        result = request_leave(employee_id, leave_data)
        
        if result['success']:
            return jsonify({"success": True, "leave_request_id": result['leave_request_id'], "message": "Leave request submitted successfully"}), 201
        else:
            return jsonify({"success": False, "error": result.get('error', 'Failed to submit leave request')}), 400
    except Exception as e:
        current_app.logger.exception(f"Error requesting leave via API: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


@hr_bp.route("/api/payroll/export", methods=["GET"])
@login_required
@role_required(UserRole.Admin, UserRole.SalesManager)
def api_payroll_export():
    """API: Generate payroll export."""
    try:
        period_start = request.args.get('start')
        period_end = request.args.get('end')
        
        if not period_start or not period_end:
            return jsonify({"success": False, "error": "start and end date parameters are required (YYYY-MM-DD)"}), 400
        
        result = generate_payroll_export(period_start, period_end, current_user.id)
        
        if result['success']:
            return jsonify({
                "success": True,
                "export_id": result['export_id'],
                "file_path": result['file_path'],
                "message": "Payroll export generated successfully"
            }), 200
        else:
            return jsonify({"success": False, "error": result.get('error', 'Failed to generate payroll export')}), 500
    except Exception as e:
        current_app.logger.exception(f"Error generating payroll export via API: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


@hr_bp.route("/api/leave/<int:leave_id>/approve", methods=["POST"])
@login_required
@role_required(UserRole.Admin)
def api_approve_leave(leave_id):
    """API: Approve leave request."""
    try:
        leave_request = LeaveRequest.query.get_or_404(leave_id)
        leave_request.status = 'approved'
        leave_request.approver_id = current_user.id
        leave_request.approved_at = datetime.utcnow()
        db.session.commit()
        
        return jsonify({"success": True, "message": "Leave request approved"}), 200
    except Exception as e:
        db.session.rollback()
        current_app.logger.exception(f"Error approving leave: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


@hr_bp.route("/api/leave/<int:leave_id>/reject", methods=["POST"])
@login_required
@role_required(UserRole.Admin)
def api_reject_leave(leave_id):
    """API: Reject leave request."""
    try:
        leave_request = LeaveRequest.query.get_or_404(leave_id)
        leave_request.status = 'rejected'
        leave_request.approver_id = current_user.id
        leave_request.approved_at = datetime.utcnow()
        leave_request.rejection_reason = request.get_json().get('reason', '') if request.is_json else request.form.get('reason', '')
        db.session.commit()
        
        return jsonify({"success": True, "message": "Leave request rejected"}), 200
    except Exception as e:
        db.session.rollback()
        current_app.logger.exception(f"Error rejecting leave: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


@hr_bp.route("/api/attendance/<int:attendance_id>/approve", methods=["POST"])
@login_required
@role_required(UserRole.Admin)
def api_approve_attendance(attendance_id):
    """API: Approve attendance record."""
    try:
        attendance = Attendance.query.get_or_404(attendance_id)
        attendance.approved = True
        attendance.approved_by = current_user.id
        attendance.approved_at = datetime.utcnow()
        db.session.commit()
        
        return jsonify({"success": True, "message": "Attendance approved"}), 200
    except Exception as e:
        db.session.rollback()
        current_app.logger.exception(f"Error approving attendance: {e}")
        return jsonify({"success": False, "error": str(e)}), 500

