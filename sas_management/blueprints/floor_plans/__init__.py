"""Floor Plan Builder Blueprint - Modern drag-and-drop floor plan designer."""
from datetime import datetime
import json

from flask import Blueprint, jsonify, redirect, render_template, request, url_for
from flask_login import current_user, login_required

from models import FloorPlan, Event, db

floor_plans_bp = Blueprint("floor_plans_bp", __name__, url_prefix="/")


@floor_plans_bp.route("/floor-plans/")
@floor_plans_bp.route("/floor-plans/list")
@login_required
def list():
    """List all floor plans."""
    try:
        search_query = request.args.get("search", "").strip()
        event_id = request.args.get("event_id", type=int)
        
        query = FloorPlan.query
        if event_id:
            query = query.filter_by(event_id=event_id)
        
        if search_query:
            from sqlalchemy import or_
            query = query.join(Event).filter(
                or_(
                    FloorPlan.name.ilike(f"%{search_query}%"),
                    Event.title.ilike(f"%{search_query}%")
                )
            )
        
        floor_plans = query.order_by(FloorPlan.updated_at.desc()).all()
        
        return render_template("floor_plans/list.html", floor_plans=floor_plans, search_query=search_query, event_id=event_id)
    except Exception as e:
        from flask import current_app
        current_app.logger.exception(f"Error loading floor plans list: {e}")
        return render_template("floor_plans/list.html", floor_plans=[], search_query="", event_id=None)


@floor_plans_bp.route("/floor-plans/new")
@login_required
def new():
    """Create a new floor plan - show the builder interface or auto-create if event_id provided."""
    event_id = request.args.get("event_id", type=int)
    event = None
    
    if event_id:
        event = Event.query.get(event_id)
        if event:
            # Check if floor plan already exists for this event
            existing = FloorPlan.query.filter_by(event_id=event_id).first()
            if existing:
                # Redirect to edit existing floor plan
                return redirect(url_for("floor_plans_bp.edit_floor_plan", id=existing.id))
            
            # Auto-create new floor plan for this event
            name = f"Floor Plan - {event.title}"
            default_data = '{"objects": [], "meta": {}}'
            floor_plan = FloorPlan(
                name=name,
                data=default_data,  # Primary field
                layout_json=default_data,  # Keep for compatibility
                event_id=event_id,
                created_by=current_user.id if hasattr(FloorPlan, 'created_by') else None
            )
            db.session.add(floor_plan)
            db.session.commit()
            # Redirect to edit immediately
            return redirect(url_for("floor_plans_bp.edit_floor_plan", id=floor_plan.id))
    
    # Get all events for assign modal
    events = Event.query.order_by(Event.date.desc()).limit(50).all()
    
    return render_template("floor_plans/new.html", event=event, events=events)


@floor_plans_bp.route("/floor-plans/create", methods=["POST"])
@login_required
def create():
    """Create a new floor plan and redirect to editor immediately."""
    try:
        event_id = request.json.get("event_id") if request.is_json else request.form.get("event_id", type=int)
        name = None
        if request.is_json:
            name = request.json.get("name", "").strip() or None
        else:
            name = request.form.get("name", "").strip() or None
        
        # Check if floor plan already exists for this event
        if event_id:
            existing = FloorPlan.query.filter_by(event_id=event_id).first()
            if existing:
                return jsonify({
                    "success": True,
                    "floor_plan_id": existing.id,
                    "redirect": url_for("floor_plans_bp.edit_floor_plan", id=existing.id)
                })
        
        # Generate default name if not provided
        if not name and event_id:
            event = Event.query.get(event_id)
            if event:
                name = f"Floor Plan - {event.title}"
        
        if not name:
            name = f"Floor Plan - {datetime.now().strftime('%Y-%m-%d %H:%M')}"
        
        # Create new floor plan
        default_data = '{"objects": [], "meta": {}}'
        floor_plan = FloorPlan(
            name=name,
            data=default_data,  # Primary field
            layout_json=default_data,  # Keep for compatibility
            event_id=event_id if event_id else None,
            created_by=current_user.id if hasattr(FloorPlan, 'created_by') else None
        )
        
        db.session.add(floor_plan)
        db.session.commit()
        
        if request.is_json:
            return jsonify({
                "success": True,
                "floor_plan_id": floor_plan.id,
                "redirect": url_for("floor_plans_bp.edit_floor_plan", id=floor_plan.id)
            })
        else:
            return redirect(url_for("floor_plans_bp.edit_floor_plan", id=floor_plan.id))
            
    except Exception as e:
        db.session.rollback()
        if request.is_json:
            return jsonify({"success": False, "error": str(e)}), 500
        else:
            return redirect(url_for("floor_plans_bp.new"))


@floor_plans_bp.route("/floor-plans/<int:id>", endpoint="floorplan_view")
@login_required
def view_floor_plan(id):
    """View an existing floor plan."""
    try:
        fp = FloorPlan.query.get_or_404(id)
        event = fp.event if fp else None
        
        # Get floor plan JSON data - prefer data field, fallback to layout_json
        floorplan_json = fp.data if fp.data else (fp.layout_json if fp.layout_json else "")
        
        # Get all events for assign modal
        events = Event.query.order_by(Event.date.desc()).limit(50).all()
        
        return render_template(
            "floor_plans/new.html",
            floorplan=fp,
            floorplan_json=floorplan_json,
            event=event,
            events=events
        )
    except Exception as e:
        from flask import current_app, flash
        current_app.logger.exception(f"Error loading floor plan: {e}")
        flash(f"Error loading floor plan: {str(e)}", "danger")
        return redirect(url_for("floor_plans_bp.list"))


@floor_plans_bp.route("/floor-plans/<int:id>/edit", endpoint="edit_floor_plan")
@login_required
def edit_floor_plan(id):
    """Edit an existing floor plan."""
    fp = FloorPlan.query.get_or_404(id)
    return render_template(
        "floor_plans/edit.html",
        floorplan=fp,
        floorplan_json=fp.data or ""
    )


@floor_plans_bp.route("/floor-plans/save", methods=["POST"])
@login_required
def save():
    """Save floor plan data - silent save, no notifications."""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({"success": False, "error": "No data provided"}), 400
        
        plan_id = data.get("plan_id") or data.get("floor_plan_id")
        name = data.get("name", "").strip()
        canvas_data = data.get("canvas_data", {})
        event_id = data.get("event_id")
        
        # Convert canvas_data to JSON string
        layout_json = json.dumps(canvas_data) if canvas_data else '{"objects": [], "meta": {}}'
        
        # Update existing floor plan
        if plan_id:
            floor_plan = FloorPlan.query.get(plan_id)
            if floor_plan:
                if name:
                    floor_plan.name = name
                floor_plan.data = layout_json  # Primary field - save here first
                floor_plan.layout_json = layout_json  # Keep for compatibility
                floor_plan.updated_at = datetime.utcnow()
                if event_id:
                    floor_plan.event_id = event_id
                db.session.commit()
                return jsonify({"success": True, "floor_plan_id": floor_plan.id})
        
        # Create new floor plan if no plan_id provided
        if not name:
            if event_id:
                event = Event.query.get(event_id)
                if event:
                    name = f"Floor Plan - {event.title}"
            if not name:
                name = f"Floor Plan - {datetime.now().strftime('%Y-%m-%d %H:%M')}"
        
        floor_plan = FloorPlan(
            name=name,
            data=layout_json,  # Primary field - save here first
            layout_json=layout_json,  # Keep for compatibility
            event_id=event_id if event_id else None,
            created_by=current_user.id if hasattr(FloorPlan, 'created_by') else None
        )
        
        db.session.add(floor_plan)
        db.session.commit()
        
        return jsonify({"success": True, "floor_plan_id": floor_plan.id})
        
    except Exception as e:
        db.session.rollback()
        return jsonify({"success": False, "error": str(e)}), 500


@floor_plans_bp.route("/floor-plans/save/<int:id>", methods=["POST"])
@login_required
def save_floor_plan(id):
    """Save floor plan JSON data by ID."""
    fp = FloorPlan.query.get_or_404(id)
    req = request.get_json(silent=True)
    
    if req and "data" in req:
        fp.data = req["data"]
        db.session.commit()
        return jsonify({"success": True})
    
    return jsonify({"success": False}), 400


@floor_plans_bp.route("/floor-plans/open/<int:id>", endpoint="floorplan_open")
@login_required
def open_floor_plan(id):
    """Open an existing floor plan in the editor - redirects to edit."""
    try:
        # Verify floor plan exists before redirecting
        fp = FloorPlan.query.get_or_404(id)
        return redirect(url_for("floor_plans_bp.edit_floor_plan", id=id))
    except Exception as e:
        from flask import current_app, flash
        current_app.logger.exception(f"Error opening floor plan: {e}")
        flash(f"Error opening floor plan: {str(e)}", "danger")
        return redirect(url_for("floor_plans_bp.list"))


@floor_plans_bp.route("/floor-plans/<int:floor_plan_id>/view", endpoint="floorplan_view_alt")
@login_required
def view(floor_plan_id):
    """View an existing floor plan - redirects to view_floor_plan."""
    return redirect(url_for("floor_plans_bp.floorplan_view", id=floor_plan_id))


@floor_plans_bp.route("/floor-plans/export/<int:floor_plan_id>/png")
@login_required
def export_png(floor_plan_id):
    """Export floor plan as PNG (placeholder - would need canvas rendering)."""
    floor_plan = FloorPlan.query.get_or_404(floor_plan_id)
    # This would require server-side canvas rendering
    return jsonify({"message": "PNG export feature - to be implemented"})


@floor_plans_bp.route("/floor-plans/assign/<int:floor_plan_id>", methods=["POST"])
@login_required
def assign(floor_plan_id):
    """Assign floor plan to an event."""
    try:
        floor_plan = FloorPlan.query.get_or_404(floor_plan_id)
        event_id = request.json.get("event_id")
        
        if not event_id:
            return jsonify({"success": False, "error": "Event ID required"}), 400
        
        event = Event.query.get_or_404(event_id)
        floor_plan.event_id = event_id
        db.session.commit()
        
        return jsonify({
            "success": True,
            "message": f"Floor plan assigned to {event.title}"
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({"success": False, "error": str(e)}), 500

