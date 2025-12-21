"""Mobile Staff Portal routes."""
from flask import Blueprint, render_template, request, jsonify, flash, redirect, url_for
from flask_login import login_required, current_user
from datetime import datetime, date

from sas_management.models import db, Task, StaffTask

mobile_staff_bp = Blueprint("mobile_staff", __name__, url_prefix="/mobile")


@mobile_staff_bp.route("/dashboard")
@login_required
def dashboard():
    """Mobile staff dashboard."""
    # Get user's tasks
    user_tasks = Task.query.filter_by(assigned_to=current_user.id).filter_by(status='Pending').limit(10).all()
    
    # Get staff tasks
    staff_tasks = StaffTask.query.filter_by(assigned_to=current_user.id).filter_by(status='pending').limit(10).all()
    
    return render_template("mobile_staff/dashboard.html", 
        user_tasks=user_tasks, 
        staff_tasks=staff_tasks
    )


@mobile_staff_bp.route("/attendance/clock", methods=["POST"])
@login_required
def clock_attendance():
    """Clock in/out."""
    try:
        action = request.json.get('action', 'clock_in')
        # TODO: Implement attendance logging
        return jsonify({'success': True, 'action': action, 'timestamp': datetime.utcnow().isoformat()})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@mobile_staff_bp.route("/tasks")
@login_required
def tasks():
    """View tasks."""
    user_tasks = Task.query.filter_by(assigned_to=current_user.id).order_by(Task.due_date.desc()).limit(50).all()
    return render_template("mobile_staff/tasks.html", tasks=user_tasks)

