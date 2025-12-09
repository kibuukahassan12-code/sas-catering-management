"""Floor Planner Blueprint - Professional event floor plan designer."""
from datetime import datetime
import json
import base64

from flask import Blueprint, current_app, flash, jsonify, redirect, render_template, request, send_file, url_for
from flask_login import current_user, login_required
from werkzeug.utils import secure_filename
import io

from models import FloorPlan, Event, User, UserRole, db
from services.floorplanner_service import (
    create_floorplan,
    update_floorplan,
    save_thumbnail,
    get_floorplan,
    list_floorplans,
    delete_floorplan,
    export_png,
    export_pdf
)
from utils import role_required

floorplanner_bp = Blueprint("floorplanner", __name__, url_prefix="/floorplanner")


@floorplanner_bp.route("/dashboard")
@login_required
def dashboard():
    """Floor planner dashboard with all floor plans."""
    try:
        search_query = request.args.get("search", "").strip()
        
        query = FloorPlan.query.join(Event)
        if search_query:
            query = query.filter(
                db.or_(
                    FloorPlan.name.ilike(f"%{search_query}%"),
                    Event.event_name.ilike(f"%{search_query}%")
                )
            )
        
        floorplans = query.order_by(FloorPlan.updated_at.desc()).all()
        
        # Prepare thumbnails as base64 strings
        for floorplan in floorplans:
            if floorplan.thumbnail:
                try:
                    floorplan.thumbnail_b64 = base64.b64encode(floorplan.thumbnail).decode('utf-8')
                except Exception:
                    floorplan.thumbnail_b64 = None
            else:
                floorplan.thumbnail_b64 = None
        
        return render_template("floorplanner/dashboard.html", floorplans=floorplans, search_query=search_query)
    except Exception as e:
        current_app.logger.exception(f"Error loading floor planner dashboard: {e}")
        return render_template("floorplanner/dashboard.html", floorplans=[], search_query="")


@floorplanner_bp.route("/new/<int:event_id>")
@login_required
@role_required(UserRole.Admin, UserRole.SalesManager)
def new_floorplan(event_id):
    """Create a new floor plan for an event and show editor immediately."""
    try:
        event = Event.query.get_or_404(event_id)
        
        # Check if floor plan already exists
        existing = FloorPlan.query.filter_by(event_id=event_id).first()
        if existing:
            return redirect(url_for("floorplanner.editor", id=existing.id))
        
        # Create new floor plan automatically
        name = request.args.get("name", "").strip()
        if not name:
            name = None  # Service will generate default name
        
        floorplan = create_floorplan(event_id, current_user.id, name)
        return redirect(url_for("floorplanner.editor", id=floorplan.id))
    except Exception as e:
        current_app.logger.exception(f"Error creating floor plan: {e}")
        return redirect(url_for("floorplanner.dashboard"))


@floorplanner_bp.route("/create/<int:event_id>", methods=["GET", "POST"])
@login_required
@role_required(UserRole.Admin, UserRole.SalesManager)
def create(event_id):
    """Create a new floor plan (legacy route - redirects to new)."""
    # For POST requests, get name from form
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        if name:
            return redirect(url_for("floorplanner.new_floorplan", event_id=event_id, name=name))
    
    # For GET requests, just redirect to new
    return redirect(url_for("floorplanner.new_floorplan", event_id=event_id))


@floorplanner_bp.route("/<int:id>/editor")
@login_required
def editor(id):
    """Floor plan editor with Fabric.js canvas."""
    try:
        floorplan = get_floorplan(id)
        if not floorplan:
            flash("Floor plan not found.", "danger")
            return redirect(url_for("floorplanner.dashboard"))
        
        event = Event.query.get_or_404(floorplan.event_id)
        
        # Parse layout JSON - prefer data field, fallback to layout_json
        try:
            json_str = floorplan.data if floorplan.data else (floorplan.layout_json if floorplan.layout_json else None)
            layout_data = json.loads(json_str) if json_str else {"objects": [], "meta": {}}
        except json.JSONDecodeError:
            layout_data = {"objects": [], "meta": {}}
        
        return render_template(
            "floorplanner/editor.html",
            floorplan=floorplan,
            event=event,
            layout_data=json.dumps(layout_data)
        )
    except Exception as e:
        current_app.logger.exception(f"Error loading floor plan editor: {e}")
        return redirect(url_for("floorplanner.dashboard"))


@floorplanner_bp.route("/<int:id>/save", methods=["POST"])
@login_required
def save(id):
    """Save floor plan layout."""
    try:
        data = request.get_json()
        if not data or "layout" not in data:
            return jsonify({"success": False, "error": "No layout data provided"}), 400
        
        layout_json = json.dumps(data["layout"])
        update_floorplan(id, layout_json)
        
        return jsonify({"success": True, "message": "Floor plan saved successfully"})
    except Exception as e:
        current_app.logger.exception(f"Error saving floor plan: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


@floorplanner_bp.route("/<int:id>/save-thumbnail", methods=["POST"])
@login_required
def save_thumbnail_route(id):
    """Save floor plan thumbnail."""
    try:
        data = request.get_json()
        if not data or "thumbnail" not in data:
            return jsonify({"success": False, "error": "No thumbnail data provided"}), 400
        
        save_thumbnail(id, data["thumbnail"])
        
        return jsonify({"success": True, "message": "Thumbnail saved successfully"})
    except Exception as e:
        current_app.logger.exception(f"Error saving thumbnail: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


@floorplanner_bp.route("/<int:id>/delete", methods=["POST"])
@login_required
@role_required(UserRole.Admin, UserRole.SalesManager)
def delete(id):
    """Delete a floor plan."""
    try:
        delete_floorplan(id)
        flash("Floor plan deleted successfully!", "success")
        return redirect(url_for("floorplanner.dashboard"))
    except Exception as e:
        current_app.logger.exception(f"Error deleting floor plan: {e}")
        flash(f"Error deleting floor plan: {str(e)}", "danger")
        return redirect(url_for("floorplanner.dashboard"))


@floorplanner_bp.route("/<int:id>/export/png")
@login_required
def export_png_route(id):
    """Export floor plan as PNG."""
    try:
        png_data = export_png(id)
        floorplan = get_floorplan(id)
        
        return send_file(
            io.BytesIO(png_data),
            mimetype='image/png',
            as_attachment=True,
            download_name=f"floorplan_{floorplan.name.replace(' ', '_')}.png"
        )
    except Exception as e:
        current_app.logger.exception(f"Error exporting PNG: {e}")
        flash(f"Error exporting PNG: {str(e)}", "danger")
        return redirect(url_for("floorplanner.editor", id=id))


@floorplanner_bp.route("/<int:id>/export/pdf")
@login_required
def export_pdf_route(id):
    """Export floor plan as PDF."""
    try:
        pdf_data = export_pdf(id)
        floorplan = get_floorplan(id)
        
        return send_file(
            io.BytesIO(pdf_data),
            mimetype='application/pdf',
            as_attachment=True,
            download_name=f"floorplan_{floorplan.name.replace(' ', '_')}.pdf"
        )
    except Exception as e:
        current_app.logger.exception(f"Error exporting PDF: {e}")
        flash(f"Error exporting PDF: {str(e)}", "danger")
        return redirect(url_for("floorplanner.editor", id=id))

