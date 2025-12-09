"""Incident & Quality routes."""
from flask import Blueprint, render_template, request, jsonify, flash, redirect, url_for
from flask_login import login_required, current_user
from datetime import datetime

from models import db, Incident, QualityChecklist, Event, UserRole
from utils import role_required

incidents_bp = Blueprint("incidents", __name__, url_prefix="/incidents")

@incidents_bp.route("/dashboard")
@login_required
@role_required(UserRole.Admin, UserRole.SalesManager)
def dashboard():
    """Incidents dashboard."""
    open_incidents = Incident.query.filter_by(status='open').order_by(Incident.created_at.desc()).limit(20).all()
    checklists = QualityChecklist.query.all()
    return render_template("incidents/incidents_dashboard.html", incidents=open_incidents, checklists=checklists)

@incidents_bp.route("/report", methods=["GET", "POST"])
@login_required
def incident_report():
    """Report incident."""
    if request.method == "POST":
        try:
            title = request.form.get('title', '').strip()
            if not title:
                flash("Incident title is required", "danger")
                events = Event.query.order_by(Event.event_date.desc()).limit(50).all()
                return render_template("incidents/incident_report.html", events=events)
            
            incident = Incident(
                event_id=request.form.get('event_id') or None,
                reported_by=current_user.id,
                title=title,
                description=request.form.get('description', '').strip(),
                severity=request.form.get('severity', 'Medium'),
                status=request.form.get('status', 'open').title()
            )
            db.session.add(incident)
            db.session.commit()
            flash("Incident reported successfully!", "success")
            return redirect(url_for("incidents.dashboard"))
        except Exception as e:
            db.session.rollback()
            flash(f"Error reporting incident: {str(e)}", "danger")
    
    events = Event.query.order_by(Event.event_date.desc()).limit(50).all()
    return render_template("incidents/incident_report.html", events=events)

