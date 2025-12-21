"""Operational Service Management Routes - Checklist, Item Movement, Team Management."""
from datetime import datetime
from decimal import Decimal
from flask import request, redirect, url_for, flash, jsonify, abort, render_template, current_app
from flask_login import login_required
from sqlalchemy.orm import joinedload

from sas_management.models import db, UserRole
from sas_management.service.models import (
    ServiceEvent,
    ServiceChecklist,
    ServiceChecklistItemNew,
    ServiceItemMovement,
    ServiceTeamLeader,
    PartTimeServiceStaff,
    ServiceTeamAssignment,
)
from sas_management.utils import role_required
from sas_management.utils.helpers import get_or_404

# Import the service blueprint from routes
from sas_management.blueprints.service.routes import service_bp


# ============================================================================
# CHECKLIST MANAGEMENT
# ============================================================================

@service_bp.route("/events/<int:event_id>/checklists", methods=["POST"])
@login_required
@role_required(UserRole.Admin, UserRole.SalesManager)
def checklist_create(event_id):
    """Create a new checklist for an event."""
    try:
        event = get_or_404(ServiceEvent, event_id)
        
        phase = request.form.get("phase", "pre_event")
        title = request.form.get("title", "").strip()
        assigned_staff = request.form.get("assigned_staff", "").strip()
        
        if not title:
            flash("Checklist title is required.", "danger")
            return redirect(url_for("service.event_view", event_id=event_id, tab="checklist"))
        
        checklist = ServiceChecklist(
            service_event_id=event_id,
            phase=phase,
            title=title,
            assigned_staff=assigned_staff or None
        )
        
        db.session.add(checklist)
        db.session.commit()
        
        flash("Checklist created successfully.", "success")
        return redirect(url_for("service.event_view", event_id=event_id, tab="checklist"))
        
    except Exception as e:
        current_app.logger.error(f"Error creating checklist: {e}")
        db.session.rollback()
        flash("Error creating checklist.", "danger")
        return redirect(url_for("service.event_view", event_id=event_id))


@service_bp.route("/events/<int:event_id>/checklists/<int:checklist_id>/items", methods=["POST"])
@login_required
@role_required(UserRole.Admin, UserRole.SalesManager)
def checklist_item_add(event_id, checklist_id):
    """Add an item to a checklist."""
    try:
        event = get_or_404(ServiceEvent, event_id)
        checklist = get_or_404(ServiceChecklist, checklist_id)
        
        if checklist.service_event_id != event_id:
            abort(404)
        
        description = request.form.get("description", "").strip()
        if not description:
            flash("Item description is required.", "danger")
            return redirect(url_for("service.event_view", event_id=event_id, tab="checklist"))
        
        item = ServiceChecklistItemNew(
            checklist_id=checklist_id,
            description=description
        )
        
        db.session.add(item)
        db.session.commit()
        
        flash("Checklist item added.", "success")
        return redirect(url_for("service.event_view", event_id=event_id, tab="checklist"))
        
    except Exception as e:
        current_app.logger.error(f"Error adding checklist item: {e}")
        db.session.rollback()
        flash("Error adding checklist item.", "danger")
        return redirect(url_for("service.event_view", event_id=event_id))


@service_bp.route("/events/<int:event_id>/checklists/<int:checklist_id>/items/<int:item_id>/toggle", methods=["POST"])
@login_required
@role_required(UserRole.Admin, UserRole.SalesManager)
def checklist_item_toggle(event_id, checklist_id, item_id):
    """Toggle checklist item completion."""
    try:
        event = get_or_404(ServiceEvent, event_id)
        checklist = get_or_404(ServiceChecklist, checklist_id)
        item = get_or_404(ServiceChecklistItemNew, item_id)
        
        if checklist.service_event_id != event_id or item.checklist_id != checklist_id:
            abort(404)
        
        item.is_done = not item.is_done
        item.updated_at = datetime.utcnow()
        
        # Update checklist completion status
        all_items = ServiceChecklistItemNew.query.filter_by(checklist_id=checklist_id).all()
        all_done = all(item.is_done for item in all_items) if all_items else False
        checklist.is_completed = all_done
        if all_done and not checklist.completed_at:
            checklist.completed_at = datetime.utcnow()
        elif not all_done:
            checklist.completed_at = None
        
        db.session.commit()
        
        if request.is_json:
            return jsonify({"success": True, "is_done": item.is_done, "checklist_completed": checklist.is_completed})
        
        flash("Checklist item updated.", "success")
        return redirect(url_for("service.event_view", event_id=event_id, tab="checklist"))
        
    except Exception as e:
        current_app.logger.error(f"Error toggling checklist item: {e}")
        db.session.rollback()
        if request.is_json:
            return jsonify({"success": False, "error": str(e)}), 500
        flash("Error updating checklist item.", "danger")
        return redirect(url_for("service.event_view", event_id=event_id))


@service_bp.route("/events/<int:event_id>/checklists/<int:checklist_id>/complete", methods=["POST"])
@login_required
@role_required(UserRole.Admin, UserRole.SalesManager)
def checklist_complete(event_id, checklist_id):
    """Mark checklist as completed (Team Leader action)."""
    try:
        event = get_or_404(ServiceEvent, event_id)
        checklist = get_or_404(ServiceChecklist, checklist_id)
        
        if checklist.service_event_id != event_id:
            abort(404)
        
        checklist.is_completed = True
        checklist.completed_at = datetime.utcnow()
        
        db.session.commit()
        
        flash("Checklist marked as completed.", "success")
        return redirect(url_for("service.event_view", event_id=event_id, tab="checklist"))
        
    except Exception as e:
        current_app.logger.error(f"Error completing checklist: {e}")
        db.session.rollback()
        flash("Error completing checklist.", "danger")
        return redirect(url_for("service.event_view", event_id=event_id))


# ============================================================================
# ITEM MOVEMENT TRACKING
# ============================================================================

@service_bp.route("/events/<int:event_id>/items/movement", methods=["POST"])
@login_required
@role_required(UserRole.Admin, UserRole.SalesManager)
def item_movement_create(event_id):
    """Create or update item movement record."""
    try:
        event = get_or_404(ServiceEvent, event_id)
        
        item_name = request.form.get("item_name", "").strip()
        quantity_taken = int(request.form.get("quantity_taken", 0) or 0)
        quantity_returned = int(request.form.get("quantity_returned", 0) or 0)
        condition_notes = request.form.get("condition_notes", "").strip()
        
        if not item_name:
            flash("Item name is required.", "danger")
            return redirect(url_for("service.event_view", event_id=event_id, tab="items"))
        
        # Check if movement record exists
        movement = ServiceItemMovement.query.filter_by(
            service_event_id=event_id,
            item_name=item_name
        ).first()
        
        if movement:
            movement.quantity_taken = quantity_taken
            movement.quantity_returned = quantity_returned
            movement.condition_notes = condition_notes
            movement.update_status()
        else:
            movement = ServiceItemMovement(
                service_event_id=event_id,
                item_name=item_name,
                quantity_taken=quantity_taken,
                quantity_returned=quantity_returned,
                condition_notes=condition_notes
            )
            movement.update_status()
            db.session.add(movement)
        
        db.session.commit()
        
        flash("Item movement recorded.", "success")
        return redirect(url_for("service.event_view", event_id=event_id, tab="items"))
        
    except Exception as e:
        current_app.logger.error(f"Error recording item movement: {e}")
        db.session.rollback()
        flash("Error recording item movement.", "danger")
        return redirect(url_for("service.event_view", event_id=event_id))


@service_bp.route("/events/<int:event_id>/items/<int:movement_id>/return", methods=["POST"])
@login_required
@role_required(UserRole.Admin, UserRole.SalesManager)
def item_movement_return(event_id, movement_id):
    """Update returned quantity for an item."""
    try:
        event = get_or_404(ServiceEvent, event_id)
        movement = get_or_404(ServiceItemMovement, movement_id)
        
        if movement.service_event_id != event_id:
            abort(404)
        
        quantity_returned = int(request.form.get("quantity_returned", 0) or 0)
        condition_notes = request.form.get("condition_notes", "").strip()
        
        movement.quantity_returned = quantity_returned
        if condition_notes:
            movement.condition_notes = condition_notes
        movement.update_status()
        
        db.session.commit()
        
        if request.is_json:
            return jsonify({
                "success": True,
                "status": movement.status,
                "quantity_returned": movement.quantity_returned
            })
        
        flash("Item return updated.", "success")
        return redirect(url_for("service.event_view", event_id=event_id, tab="items"))
        
    except Exception as e:
        current_app.logger.error(f"Error updating item return: {e}")
        db.session.rollback()
        if request.is_json:
            return jsonify({"success": False, "error": str(e)}), 500
        flash("Error updating item return.", "danger")
        return redirect(url_for("service.event_view", event_id=event_id))


# ============================================================================
# TEAM LEADER MANAGEMENT
# ============================================================================

@service_bp.route("/events/<int:event_id>/team-leader", methods=["POST"])
@login_required
@role_required(UserRole.Admin, UserRole.SalesManager)
def team_leader_create(event_id):
    """Assign team leader to an event."""
    try:
        event = get_or_404(ServiceEvent, event_id)
        
        staff_name = request.form.get("staff_name", "").strip()
        phone = request.form.get("phone", "").strip()
        responsibilities = request.form.get("responsibilities", "").strip()
        
        if not staff_name:
            flash("Team leader name is required.", "danger")
            return redirect(url_for("service.event_view", event_id=event_id, tab="team"))
        
        # Check if team leader already exists for this event
        existing = ServiceTeamLeader.query.filter_by(service_event_id=event_id).first()
        
        if existing:
            existing.staff_name = staff_name
            existing.phone = phone or None
            existing.responsibilities = responsibilities or None
            existing.updated_at = datetime.utcnow()
        else:
            leader = ServiceTeamLeader(
                service_event_id=event_id,
                staff_name=staff_name,
                phone=phone or None,
                responsibilities=responsibilities or None
            )
            db.session.add(leader)
        
        db.session.commit()
        
        flash("Team leader assigned.", "success")
        return redirect(url_for("service.event_view", event_id=event_id, tab="team"))
        
    except Exception as e:
        current_app.logger.error(f"Error assigning team leader: {e}")
        db.session.rollback()
        flash("Error assigning team leader.", "danger")
        return redirect(url_for("service.event_view", event_id=event_id))


@service_bp.route("/events/<int:event_id>/team-leader/<int:leader_id>", methods=["POST"])
@login_required
@role_required(UserRole.Admin, UserRole.SalesManager)
def team_leader_update(event_id, leader_id):
    """Update team leader information."""
    try:
        event = get_or_404(ServiceEvent, event_id)
        leader = get_or_404(ServiceTeamLeader, leader_id)
        
        if leader.service_event_id != event_id:
            abort(404)
        
        leader.staff_name = request.form.get("staff_name", "").strip()
        leader.phone = request.form.get("phone", "").strip() or None
        leader.responsibilities = request.form.get("responsibilities", "").strip() or None
        leader.updated_at = datetime.utcnow()
        
        db.session.commit()
        
        flash("Team leader updated.", "success")
        return redirect(url_for("service.event_view", event_id=event_id, tab="team"))
        
    except Exception as e:
        current_app.logger.error(f"Error updating team leader: {e}")
        db.session.rollback()
        flash("Error updating team leader.", "danger")
        return redirect(url_for("service.event_view", event_id=event_id))


# ============================================================================
# PART-TIME STAFF MANAGEMENT
# ============================================================================

@service_bp.route("/part-time-staff", methods=["GET", "POST"])
@login_required
@role_required(UserRole.Admin, UserRole.SalesManager)
def part_time_staff_list():
    """List and create part-time staff."""
    if request.method == "POST":
        try:
            full_name = request.form.get("full_name", "").strip()
            phone = request.form.get("phone", "").strip()
            role = request.form.get("role", "").strip()
            pay_rate = request.form.get("pay_rate", "0") or "0"
            
            if not full_name:
                flash("Full name is required.", "danger")
                return redirect(url_for("service.part_time_staff_list"))
            
            staff = PartTimeServiceStaff(
                full_name=full_name,
                phone=phone or None,
                role=role or None,
                pay_rate=Decimal(pay_rate) if pay_rate else None,
                is_active=True
            )
            
            db.session.add(staff)
            db.session.commit()
            
            flash("Part-time staff added.", "success")
            return redirect(url_for("service.part_time_staff_list"))
            
        except Exception as e:
            current_app.logger.error(f"Error creating part-time staff: {e}")
            db.session.rollback()
            flash("Error creating part-time staff.", "danger")
            return redirect(url_for("service.part_time_staff_list"))
    
    # GET request - list staff
    try:
        staff_list = PartTimeServiceStaff.query.filter_by(is_active=True).order_by(PartTimeServiceStaff.full_name.asc()).all()
        return render_template("service/part_time_staff.html", staff_list=staff_list)
    except Exception as e:
        current_app.logger.error(f"Error listing part-time staff: {e}")
        return render_template("service/part_time_staff.html", staff_list=[])


@service_bp.route("/events/<int:event_id>/team/assign", methods=["POST"])
@login_required
@role_required(UserRole.Admin, UserRole.SalesManager)
def team_assign(event_id):
    """Assign part-time staff to an event."""
    try:
        event = get_or_404(ServiceEvent, event_id)
        
        staff_id = request.form.get("staff_id")
        attendance_status = request.form.get("attendance_status", "pending")
        
        if not staff_id:
            flash("Staff selection is required.", "danger")
            return redirect(url_for("service.event_view", event_id=event_id, tab="team"))
        
        # Check if already assigned
        existing = ServiceTeamAssignment.query.filter_by(
            service_event_id=event_id,
            staff_id=staff_id
        ).first()
        
        if existing:
            existing.attendance_status = attendance_status
            existing.updated_at = datetime.utcnow()
        else:
            assignment = ServiceTeamAssignment(
                service_event_id=event_id,
                staff_id=int(staff_id),
                attendance_status=attendance_status
            )
            db.session.add(assignment)
        
        db.session.commit()
        
        flash("Staff assigned to event.", "success")
        return redirect(url_for("service.event_view", event_id=event_id, tab="team"))
        
    except Exception as e:
        current_app.logger.error(f"Error assigning staff: {e}")
        db.session.rollback()
        flash("Error assigning staff.", "danger")
        return redirect(url_for("service.event_view", event_id=event_id))


@service_bp.route("/events/<int:event_id>/team/<int:assignment_id>/attendance", methods=["POST"])
@login_required
@role_required(UserRole.Admin, UserRole.SalesManager)
def team_attendance_update(event_id, assignment_id):
    """Update attendance status for assigned staff."""
    try:
        event = get_or_404(ServiceEvent, event_id)
        assignment = get_or_404(ServiceTeamAssignment, assignment_id)
        
        if assignment.service_event_id != event_id:
            abort(404)
        
        attendance_status = request.form.get("attendance_status") or (request.get_json().get("attendance_status") if request.is_json else None)
        
        if attendance_status:
            assignment.attendance_status = attendance_status
            assignment.updated_at = datetime.utcnow()
            db.session.commit()
            
            if request.is_json:
                return jsonify({"success": True, "attendance_status": attendance_status})
            
            flash("Attendance status updated.", "success")
        
        return redirect(url_for("service.event_view", event_id=event_id, tab="team"))
        
    except Exception as e:
        current_app.logger.error(f"Error updating attendance: {e}")
        db.session.rollback()
        if request.is_json:
            return jsonify({"success": False, "error": str(e)}), 500
        flash("Error updating attendance.", "danger")
        return redirect(url_for("service.event_view", event_id=event_id))


@service_bp.route("/events/<int:event_id>/team/<int:assignment_id>/remove", methods=["POST"])
@login_required
@role_required(UserRole.Admin, UserRole.SalesManager)
def team_assign_remove(event_id, assignment_id):
    """Remove staff assignment from event."""
    try:
        event = get_or_404(ServiceEvent, event_id)
        assignment = get_or_404(ServiceTeamAssignment, assignment_id)
        
        if assignment.service_event_id != event_id:
            abort(404)
        
        db.session.delete(assignment)
        db.session.commit()
        
        flash("Staff assignment removed.", "success")
        return redirect(url_for("service.event_view", event_id=event_id, tab="team"))
        
    except Exception as e:
        current_app.logger.error(f"Error removing assignment: {e}")
        db.session.rollback()
        flash("Error removing assignment.", "danger")
        return redirect(url_for("service.event_view", event_id=event_id))

