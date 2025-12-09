"""Food Safety routes."""
from flask import Blueprint, render_template, request, jsonify, flash, redirect, url_for
from flask_login import login_required, current_user
from datetime import datetime
from decimal import Decimal

from models import db, HACCPChecklist, TemperatureLog, SafetyIncident, UserRole
from utils import role_required, permission_required

food_safety_bp = Blueprint("food_safety", __name__, url_prefix="/food-safety")

@food_safety_bp.route("/dashboard")
@login_required
# @permission_required("food_safety")
def dashboard():
    """Food safety dashboard."""
    checklists = HACCPChecklist.query.all()
    recent_logs = TemperatureLog.query.order_by(TemperatureLog.recorded_at.desc()).limit(20).all()
    open_incidents = SafetyIncident.query.filter_by(status='open').limit(10).all()
    
    return render_template("food_safety/haccp_dashboard.html",
        checklists=checklists,
        recent_logs=recent_logs,
        incidents=open_incidents
    )

@food_safety_bp.route("/temperature/log", methods=["POST"])
@login_required
def log_temperature():
    """Log temperature reading."""
    try:
        log = TemperatureLog(
            item=request.form.get('item', ''),
            temp_c=Decimal(request.form.get('temp_c', 0)),
            location=request.form.get('location', ''),
            notes=request.form.get('notes', ''),
            recorded_by=current_user.id
        )
        db.session.add(log)
        db.session.commit()
        
        flash("Temperature logged successfully!", "success")
        return jsonify({'success': True})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500

@food_safety_bp.route("/reports")
@login_required
@role_required(UserRole.Admin, UserRole.KitchenStaff)
def reports():
    """Food safety reports."""
    # Get date filters
    start_date = request.args.get('start')
    end_date = request.args.get('end')
    
    # Build query for logs
    logs_query = TemperatureLog.query
    if start_date:
        try:
            start = datetime.strptime(start_date, '%Y-%m-%d').date()
            logs_query = logs_query.filter(TemperatureLog.log_date >= start)
        except ValueError:
            pass
    if end_date:
        try:
            end = datetime.strptime(end_date, '%Y-%m-%d').date()
            logs_query = logs_query.filter(TemperatureLog.log_date <= end)
        except ValueError:
            pass
    
    logs = logs_query.order_by(TemperatureLog.recorded_at.desc()).limit(100).all()
    
    # Build query for incidents
    incidents_query = SafetyIncident.query
    if start_date:
        try:
            start = datetime.strptime(start_date, '%Y-%m-%d').date()
            incidents_query = incidents_query.filter(db.cast(SafetyIncident.created_at, db.Date) >= start)
        except ValueError:
            pass
    if end_date:
        try:
            end = datetime.strptime(end_date, '%Y-%m-%d').date()
            incidents_query = incidents_query.filter(db.cast(SafetyIncident.created_at, db.Date) <= end)
        except ValueError:
            pass
    
    incidents = incidents_query.order_by(SafetyIncident.created_at.desc()).limit(50).all()
    
    # Format data for template (add item_name and user names)
    formatted_logs = []
    for log in logs:
        formatted_logs.append({
            'item_name': log.location or 'N/A',  # Use location as item name
            'temperature': float(log.temperature) if log.temperature else 0,
            'recorded_by': log.recorder.email if log.recorder else 'Unknown',
            'recorded_at': log.recorded_at
        })
    
    formatted_incidents = []
    for inc in incidents:
        formatted_incidents.append({
            'description': inc.description,
            'status': inc.status,
            'reported_by': inc.reporter.email if inc.reporter else 'Unknown',
            'created_at': inc.created_at
        })
    
    return render_template("food_safety/reports.html", 
                         logs=formatted_logs, 
                         incidents=formatted_incidents)

