"""
SAS Best Foods - Industry-Grade Events Module
Complete event management system with timeline, staffing, costing, logistics, and more.
"""
from datetime import datetime, date, timedelta
from decimal import Decimal
import os
import json

from flask import (
    Blueprint, current_app, flash, jsonify, redirect, render_template, 
    request, send_from_directory, url_for, send_file, make_response
)
from flask_login import current_user, login_required
from werkzeug.utils import secure_filename
from sqlalchemy import func, or_

from models import (
    Event, EventStatus, EventTimeline, EventStaffAssignment, EventChecklistItem,
    Venue, MenuPackage, Vendor, EventVendorAssignment,
    db
)
from utils import paginate_query, get_decimal
from utils.helpers import parse_date
from utils.pdf_generator import generate_event_brief_pdf

events_bp = Blueprint("events", __name__, url_prefix="/events")


# ============================================================================
# EVENT LIST & VIEW
# ============================================================================

@events_bp.route("/")
@events_bp.route("/list")
@login_required
def events_list():
    """List all events with filters."""
    status_filter = request.args.get("status", "")
    search_query = request.args.get("search", "")
    
    query = Event.query
    
    if status_filter:
        try:
            query = query.filter(Event.status == EventStatus[status_filter])
        except (KeyError, ValueError):
            pass
    
    if search_query:
        query = query.filter(
            or_(
                Event.title.ilike(f"%{search_query}%"),
                Event.client_name.ilike(f"%{search_query}%"),
                Event.client_email.ilike(f"%{search_query}%")
            )
        )
    
    query = query.order_by(Event.date.desc(), Event.created_at.desc())
    pagination = paginate_query(query)
    
    return render_template(
        "events/list.html",
        events=pagination.items,
        pagination=pagination,
        status_filter=status_filter,
        search_query=search_query,
        EventStatus=EventStatus
    )


@events_bp.route("/<int:event_id>")
@login_required
def event_view(event_id):
    """View event details."""
    event = Event.query.get_or_404(event_id)
    
    # Calculate costs
    staff_cost = sum(
        (assignment.assigned_hours or 0) * 10000  # Assuming 10,000 UGX per hour
        for assignment in event.staff_assignments
    )
    vendor_cost = sum(
        (assignment.cost or 0) for assignment in event.vendor_assignments
    )
    
    return render_template(
        "events/view.html",
        event=event,
        staff_cost=staff_cost,
        vendor_cost=vendor_cost,
        EventStatus=EventStatus
    )


# ============================================================================
# EVENT CREATE & EDIT
# ============================================================================

@events_bp.route("/create", methods=["GET", "POST"])
@login_required
def event_create():
    """Create a new event."""
    venues = Venue.query.order_by(Venue.name.asc()).all()
    menu_packages = MenuPackage.query.order_by(MenuPackage.name.asc()).all()
    
    if request.method == "POST":
        event = Event(
            title=request.form.get("title", "").strip(),
            client_name=request.form.get("client_name", "").strip(),
            client_phone=request.form.get("client_phone", "").strip(),
            client_email=request.form.get("client_email", "").strip(),
            event_type=request.form.get("event_type", "").strip(),
            venue_id=request.form.get("venue_id", type=int) or None,
            date=parse_date(request.form.get("date")) or date.today(),
            start_time=request.form.get("start_time", "").strip(),
            end_time=request.form.get("end_time", "").strip(),
            guest_count=request.form.get("guest_count", type=int) or 0,
            menu_package_id=request.form.get("menu_package_id", type=int) or None,
            budget_estimate=get_decimal(request.form.get("budget_estimate")),
            notes=request.form.get("notes", "").strip(),
            status=EventStatus.NotStarted
        )
        
        event.labor_cost = float(request.form.get("labor_cost", 0))
        event.transport_cost = float(request.form.get("transport_cost", 0))
        event.equipment_cost = float(request.form.get("equipment_cost", 0))
        event.ingredients_cost = float(request.form.get("ingredients_cost", 0))
        event.quoted_value = float(request.form.get("quoted_value", 0))
        
        event.calculate_costs()
        
        db.session.add(event)
        db.session.commit()
        flash(f"Event '{event.title}' created successfully.", "success")
        return redirect(url_for("events.event_view", event_id=event.id))
    
    return render_template(
        "events/form.html",
        event=None,
        venues=venues,
        menu_packages=menu_packages,
        EventStatus=EventStatus
    )


@events_bp.route("/<int:event_id>/edit", methods=["GET", "POST"])
@login_required
def event_edit(event_id):
    """Edit an event."""
    event = Event.query.get_or_404(event_id)
    venues = Venue.query.order_by(Venue.name.asc()).all()
    menu_packages = MenuPackage.query.order_by(MenuPackage.name.asc()).all()
    
    if request.method == "POST":
        event.title = request.form.get("title", "").strip()
        event.client_name = request.form.get("client_name", "").strip()
        event.client_phone = request.form.get("client_phone", "").strip()
        event.client_email = request.form.get("client_email", "").strip()
        event.event_type = request.form.get("event_type", "").strip()
        event.venue_id = request.form.get("venue_id", type=int) or None
        event.date = parse_date(request.form.get("date")) or event.date
        event.start_time = request.form.get("start_time", "").strip()
        event.end_time = request.form.get("end_time", "").strip()
        event.guest_count = request.form.get("guest_count", type=int) or 0
        event.menu_package_id = request.form.get("menu_package_id", type=int) or None
        event.budget_estimate = get_decimal(request.form.get("budget_estimate"))
        event.notes = request.form.get("notes", "").strip()
        
        event.labor_cost = float(request.form.get("labor_cost", 0))
        event.transport_cost = float(request.form.get("transport_cost", 0))
        event.equipment_cost = float(request.form.get("equipment_cost", 0))
        event.ingredients_cost = float(request.form.get("ingredients_cost", 0))
        event.quoted_value = float(request.form.get("quoted_value", 0))
        
        event.calculate_costs()
        
        db.session.commit()
        flash(f"Event '{event.title}' updated successfully.", "success")
        return redirect(url_for("events.event_view", event_id=event.id))
    
    return render_template(
        "events/form.html",
        event=event,
        venues=venues,
        menu_packages=menu_packages,
        EventStatus=EventStatus
    )


@events_bp.route("/<int:event_id>/delete", methods=["POST"])
@login_required
def event_delete(event_id):
    """Delete an event."""
    event = Event.query.get_or_404(event_id)
    title = event.title
    db.session.delete(event)
    db.session.commit()
    flash(f"Event '{title}' deleted successfully.", "info")
    return redirect(url_for("events.events_list"))


@events_bp.route("/<int:event_id>/update-status", methods=["POST"])
@login_required
def event_update_status(event_id):
    """Update event status."""
    event = Event.query.get_or_404(event_id)
    status_str = request.form.get("status", "")
    
    try:
        event.status = EventStatus[status_str]
        db.session.commit()
        flash(f"Event status updated to '{event.status.value}'.", "success")
    except (KeyError, ValueError):
        flash("Invalid status.", "danger")
    
    return redirect(url_for("events.event_view", event_id=event.id))


# ============================================================================
# EVENT TIMELINE
# ============================================================================

@events_bp.route("/<int:event_id>/timeline")
@login_required
def event_timeline(event_id):
    """View and manage event timeline."""
    event = Event.query.get_or_404(event_id)
    timelines = event.timelines
    
    return render_template(
        "events/timeline.html",
        event=event,
        timelines=timelines
    )


@events_bp.route("/<int:event_id>/timeline/add", methods=["POST"])
@login_required
def timeline_add(event_id):
    """Add timeline milestone."""
    event = Event.query.get_or_404(event_id)
    
    timeline = EventTimeline(
        event_id=event.id,
        phase=request.form.get("phase", "").strip(),
        description=request.form.get("description", "").strip(),
        due_date=parse_date(request.form.get("due_date")),
        completed=False
    )
    
    db.session.add(timeline)
    db.session.commit()
    flash("Timeline milestone added.", "success")
    return redirect(url_for("events.event_timeline", event_id=event.id))


@events_bp.route("/<int:event_id>/timeline/<int:timeline_id>/toggle", methods=["POST"])
@login_required
def timeline_toggle(event_id, timeline_id):
    """Toggle timeline milestone completion."""
    timeline = EventTimeline.query.get_or_404(timeline_id)
    timeline.completed = not timeline.completed
    timeline.completed_at = datetime.utcnow() if timeline.completed else None
    db.session.commit()
    return jsonify({"completed": timeline.completed})


@events_bp.route("/<int:event_id>/timeline/<int:timeline_id>/delete", methods=["POST"])
@login_required
def timeline_delete(event_id, timeline_id):
    """Delete timeline milestone."""
    timeline = EventTimeline.query.get_or_404(timeline_id)
    db.session.delete(timeline)
    db.session.commit()
    flash("Timeline milestone deleted.", "info")
    return redirect(url_for("events.event_timeline", event_id=event.id))


# ============================================================================
# STAFFING
# ============================================================================

@events_bp.route("/<int:event_id>/staffing")
@login_required
def event_staffing(event_id):
    """View and manage staff assignments."""
    event = Event.query.get_or_404(event_id)
    
    return render_template(
        "events/staffing.html",
        event=event,
        assignments=event.staff_assignments
    )


@events_bp.route("/<int:event_id>/staffing/add", methods=["POST"])
@login_required
def staffing_add(event_id):
    """Add staff assignment."""
    event = Event.query.get_or_404(event_id)
    
    assignment = EventStaffAssignment(
        event_id=event.id,
        staff_name=request.form.get("staff_name", "").strip(),
        role=request.form.get("role", "").strip(),
        assigned_hours=get_decimal(request.form.get("assigned_hours")),
        notes=request.form.get("notes", "").strip()
    )
    
    db.session.add(assignment)
    db.session.commit()
    flash("Staff assignment added.", "success")
    return redirect(url_for("events.event_staffing", event_id=event.id))


@events_bp.route("/<int:event_id>/staffing/<int:assignment_id>/delete", methods=["POST"])
@login_required
def staffing_delete(event_id, assignment_id):
    """Delete staff assignment."""
    assignment = EventStaffAssignment.query.get_or_404(assignment_id)
    db.session.delete(assignment)
    db.session.commit()
    flash("Staff assignment removed.", "info")
    return redirect(url_for("events.event_staffing", event_id=event.id))


# ============================================================================
# COSTING & BUDGETING
# ============================================================================

@events_bp.route("/<int:event_id>/costing")
@login_required
def event_costing(event_id):
    """Event costing and budgeting page."""
    event = Event.query.get_or_404(event_id)
    
    # Calculate costs
    staff_cost = sum(
        (assignment.assigned_hours or 0) * 10000  # 10,000 UGX per hour
        for assignment in event.staff_assignments
    )
    vendor_cost = sum(
        (assignment.cost or 0) for assignment in event.vendor_assignments
    )
    
    # Menu package cost
    menu_cost = 0
    if event.menu_package_obj and event.guest_count:
        menu_cost = (event.menu_package_obj.price_per_guest or 0) * event.guest_count
    
    # Total actual cost
    total_actual = (event.actual_cost or 0) + staff_cost + vendor_cost + menu_cost
    
    return render_template(
        "events/costing.html",
        event=event,
        staff_cost=staff_cost,
        vendor_cost=vendor_cost,
        menu_cost=menu_cost,
        total_actual=total_actual
    )


@events_bp.route("/<int:event_id>/costing/update", methods=["POST"])
@login_required
def costing_update(event_id):
    """Update event costs."""
    event = Event.query.get_or_404(event_id)
    event.actual_cost = get_decimal(request.form.get("actual_cost"))
    db.session.commit()
    flash("Costing updated.", "success")
    return redirect(url_for("events.event_costing", event_id=event.id))


# ============================================================================
# LOGISTICS SHEET
# ============================================================================

@events_bp.route("/<int:event_id>/logistics")
@login_required
def event_logistics(event_id):
    """Printable logistics sheet."""
    event = Event.query.get_or_404(event_id)
    
    return render_template(
        "events/logistics.html",
        event=event
    )


# ============================================================================
# CHECKLIST
# ============================================================================

@events_bp.route("/<int:event_id>/checklist")
@login_required
def event_checklist(event_id):
    """Event checklist management."""
    event = Event.query.get_or_404(event_id)
    
    # Group items by category
    items_by_category = {}
    for item in event.checklist_items:
        category = item.category or "Misc"
        if category not in items_by_category:
            items_by_category[category] = []
        items_by_category[category].append(item)
    
    progress = event.get_checklist_progress()
    
    return render_template(
        "events/checklist.html",
        event=event,
        items_by_category=items_by_category,
        progress=progress
    )


@events_bp.route("/<int:event_id>/checklist/add", methods=["POST"])
@login_required
def checklist_add(event_id):
    """Add checklist item."""
    event = Event.query.get_or_404(event_id)
    
    item = EventChecklistItem(
        event_id=event.id,
        item_name=request.form.get("item_name", "").strip(),
        category=request.form.get("category", "Misc").strip(),
        completed=False
    )
    
    db.session.add(item)
    db.session.commit()
    flash("Checklist item added.", "success")
    return redirect(url_for("events.event_checklist", event_id=event.id))


@events_bp.route("/<int:event_id>/checklist/<int:item_id>/toggle", methods=["POST"])
@login_required
def checklist_toggle(event_id, item_id):
    """Toggle checklist item completion."""
    item = EventChecklistItem.query.get_or_404(item_id)
    item.completed = not item.completed
    item.completed_at = datetime.utcnow() if item.completed else None
    db.session.commit()
    return jsonify({"completed": item.completed})


@events_bp.route("/<int:event_id>/checklist/<int:item_id>/delete", methods=["POST"])
@login_required
def checklist_delete(event_id, item_id):
    """Delete checklist item."""
    item = EventChecklistItem.query.get_or_404(item_id)
    db.session.delete(item)
    db.session.commit()
    flash("Checklist item deleted.", "info")
    return redirect(url_for("events.event_checklist", event_id=event.id))


# ============================================================================
# VENDORS
# ============================================================================

@events_bp.route("/<int:event_id>/vendors")
@login_required
def event_vendors(event_id):
    """View and manage vendor assignments."""
    event = Event.query.get_or_404(event_id)
    all_vendors = Vendor.query.order_by(Vendor.name.asc()).all()
    
    return render_template(
        "events/vendors.html",
        event=event,
        assignments=event.vendor_assignments,
        all_vendors=all_vendors
    )


@events_bp.route("/<int:event_id>/vendors/assign", methods=["POST"])
@login_required
def vendor_assign(event_id):
    """Assign vendor to event."""
    event = Event.query.get_or_404(event_id)
    
    assignment = EventVendorAssignment(
        event_id=event.id,
        vendor_id=request.form.get("vendor_id", type=int),
        role_in_event=request.form.get("role_in_event", "").strip(),
        cost=get_decimal(request.form.get("cost")),
        notes=request.form.get("notes", "").strip()
    )
    
    db.session.add(assignment)
    db.session.commit()
    flash("Vendor assigned to event.", "success")
    return redirect(url_for("events.event_vendors", event_id=event.id))


@events_bp.route("/<int:event_id>/vendors/<int:assignment_id>/delete", methods=["POST"])
@login_required
def vendor_unassign(event_id, assignment_id):
    """Remove vendor assignment."""
    assignment = EventVendorAssignment.query.get_or_404(assignment_id)
    db.session.delete(assignment)
    db.session.commit()
    flash("Vendor assignment removed.", "info")
    return redirect(url_for("events.event_vendors", event_id=event.id))


# ============================================================================
# APPROVAL & SIGNATURE
# ============================================================================

@events_bp.route("/<int:event_id>/approval")
@login_required
def event_approval(event_id):
    """Customer approval and signature page."""
    event = Event.query.get_or_404(event_id)
    
    return render_template(
        "events/approval.html",
        event=event
    )


@events_bp.route("/<int:event_id>/approval/submit", methods=["POST"])
@login_required
def approval_submit(event_id):
    """Submit approval with signature."""
    event = Event.query.get_or_404(event_id)
    
    # Handle signature image upload
    signature_data = request.form.get("signature", "")
    if signature_data:
        # Save signature image
        import base64
        from PIL import Image
        import io
        
        try:
            # Decode base64 image
            header, encoded = signature_data.split(',', 1)
            image_data = base64.b64decode(encoded)
            
            # Save to uploads/signatures directory
            upload_dir = os.path.join(current_app.instance_path, "..", "static", "uploads", "signatures")
            os.makedirs(upload_dir, exist_ok=True)
            
            filename = f"signature_{event.id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
            filepath = os.path.join(upload_dir, filename)
            
            with open(filepath, 'wb') as f:
                f.write(image_data)
            
            event.signature_path = f"uploads/signatures/{filename}"
            event.approved_at = datetime.utcnow()
            event.status = EventStatus.Planning
            db.session.commit()
            
            flash("Event approved and signature saved.", "success")
        except Exception as e:
            current_app.logger.exception(f"Error saving signature: {e}")
            flash("Error saving signature. Please try again.", "danger")
    else:
        flash("No signature provided.", "danger")
    
    return redirect(url_for("events.event_view", event_id=event.id))


# ============================================================================
# PDF GENERATION
# ============================================================================

@events_bp.route("/<int:event_id>/brief-pdf")
@login_required
def event_brief_pdf(event_id):
    """Generate and download event brief PDF."""
    event = Event.query.get_or_404(event_id)
    
    try:
        pdf_path = generate_event_brief_pdf(event)
        return send_file(pdf_path, as_attachment=True, download_name=f"event_brief_{event.id}.pdf")
    except Exception as e:
        current_app.logger.exception(f"Error generating PDF: {e}")
        flash("Error generating PDF. Please try again.", "danger")
        return redirect(url_for("events.event_view", event_id=event.id))


# ============================================================================
# VENUE MANAGEMENT
# ============================================================================

@events_bp.route("/venues")
@login_required
def venues_list():
    """List all venues."""
    venues = Venue.query.order_by(Venue.name.asc()).all()
    return render_template("events/venues_list.html", venues=venues)


@events_bp.route("/venues/create", methods=["GET", "POST"])
@login_required
def venue_create():
    """Create a new venue."""
    if request.method == "POST":
        venue = Venue(
            name=request.form.get("name", "").strip(),
            address=request.form.get("address", "").strip(),
            layout_description=request.form.get("layout_description", "").strip(),
            capacity=request.form.get("capacity", type=int) or None,
            google_maps_link=request.form.get("google_maps_link", "").strip()
        )
        db.session.add(venue)
        db.session.commit()
        flash(f"Venue '{venue.name}' created successfully.", "success")
        return redirect(url_for("events.venues_list"))
    
    return render_template("events/venue_form.html", venue=None)


@events_bp.route("/venues/<int:venue_id>/edit", methods=["GET", "POST"])
@login_required
def venue_edit(venue_id):
    """Edit a venue."""
    venue = Venue.query.get_or_404(venue_id)
    
    if request.method == "POST":
        venue.name = request.form.get("name", "").strip()
        venue.address = request.form.get("address", "").strip()
        venue.layout_description = request.form.get("layout_description", "").strip()
        venue.capacity = request.form.get("capacity", type=int) or None
        venue.google_maps_link = request.form.get("google_maps_link", "").strip()
        db.session.commit()
        flash(f"Venue '{venue.name}' updated successfully.", "success")
        return redirect(url_for("events.venues_list"))
    
    return render_template("events/venue_form.html", venue=venue)


# ============================================================================
# MENU PACKAGE MANAGEMENT
# ============================================================================

@events_bp.route("/menu-packages")
@login_required
def menu_packages_list():
    """List all menu packages."""
    packages = MenuPackage.query.order_by(MenuPackage.name.asc()).all()
    return render_template("events/menu_packages_list.html", packages=packages)


@events_bp.route("/menu-packages/create", methods=["GET", "POST"])
@login_required
def menu_package_create():
    """Create a new menu package."""
    if request.method == "POST":
        items_json = request.form.get("items", "[]")
        try:
            items = json.loads(items_json) if items_json else []
        except json.JSONDecodeError:
            items = []
        
        package = MenuPackage(
            name=request.form.get("name", "").strip(),
            price_per_guest=get_decimal(request.form.get("price_per_guest")),
            description=request.form.get("description", "").strip(),
            items=items
        )
        db.session.add(package)
        db.session.commit()
        flash(f"Menu package '{package.name}' created successfully.", "success")
        return redirect(url_for("events.menu_packages_list"))
    
    return render_template("events/menu_package_form.html", package=None)


@events_bp.route("/menu-packages/<int:package_id>/edit", methods=["GET", "POST"])
@login_required
def menu_package_edit(package_id):
    """Edit a menu package."""
    package = MenuPackage.query.get_or_404(package_id)
    
    if request.method == "POST":
        items_json = request.form.get("items", "[]")
        try:
            items = json.loads(items_json) if items_json else []
        except json.JSONDecodeError:
            items = []
        
        package.name = request.form.get("name", "").strip()
        package.price_per_guest = get_decimal(request.form.get("price_per_guest"))
        package.description = request.form.get("description", "").strip()
        package.items = items
        db.session.commit()
        flash(f"Menu package '{package.name}' updated successfully.", "success")
        return redirect(url_for("events.menu_packages_list"))
    
    return render_template("events/menu_package_form.html", package=package)


# ============================================================================
# VENDOR MANAGEMENT
# ============================================================================

@events_bp.route("/vendors/manage")
@login_required
def vendors_manage():
    """List all vendors."""
    vendors = Vendor.query.order_by(Vendor.name.asc()).all()
    return render_template("events/vendors_manage.html", vendors=vendors)


@events_bp.route("/vendors/create", methods=["GET", "POST"])
@login_required
def vendor_create():
    """Create a new vendor."""
    if request.method == "POST":
        vendor = Vendor(
            name=request.form.get("name", "").strip(),
            service_type=request.form.get("service_type", "").strip(),
            phone=request.form.get("phone", "").strip(),
            email=request.form.get("email", "").strip(),
            notes=request.form.get("notes", "").strip()
        )
        db.session.add(vendor)
        db.session.commit()
        flash(f"Vendor '{vendor.name}' created successfully.", "success")
        return redirect(url_for("events.vendors_manage"))
    
    return render_template("events/vendor_form.html", vendor=None)


@events_bp.route("/vendors/<int:vendor_id>/edit", methods=["GET", "POST"])
@login_required
def vendor_edit(vendor_id):
    """Edit a vendor."""
    vendor = Vendor.query.get_or_404(vendor_id)
    
    if request.method == "POST":
        vendor.name = request.form.get("name", "").strip()
        vendor.service_type = request.form.get("service_type", "").strip()
        vendor.phone = request.form.get("phone", "").strip()
        vendor.email = request.form.get("email", "").strip()
        vendor.notes = request.form.get("notes", "").strip()
        db.session.commit()
        flash(f"Vendor '{vendor.name}' updated successfully.", "success")
        return redirect(url_for("events.vendors_manage"))
    
    return render_template("events/vendor_form.html", vendor=vendor)
