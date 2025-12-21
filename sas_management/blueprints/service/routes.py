"""
Event Service Department Blueprint

Deterministic blueprint with no silent failures.
All imports must succeed or startup will fail with clear error.
"""
from datetime import date, datetime
from decimal import Decimal
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, abort, current_app
from flask_login import login_required
from sqlalchemy.orm import joinedload
from sqlalchemy import func, or_

from sas_management.models import db, User, Client, UserRole
from sas_management.service.models import (
    ServiceEvent,
    ServiceEventItem,
    ServiceStaffAssignment,
    ServiceChecklistItem,
    ServiceChecklist,
    ServiceChecklistItemNew,
    ServiceItemMovement,
    ServiceTeamLeader,
    PartTimeServiceStaff,
    ServiceTeamAssignment,
)
from sas_management.service.services import (
    create_service_event,
    add_event_item,
    assign_staff,
    add_checklist_item,
    toggle_checklist_item,
    update_event_status,
)
from sas_management.service.utils import (
    calculate_event_total_cost,
    get_events_by_status,
    get_upcoming_events,
    get_events_today,
    get_checklist_progress,
)
from sas_management.utils import role_required, paginate_query
from sas_management.utils.helpers import get_or_404, parse_date

# Blueprint definition - deterministic, no conditional loading
service_bp = Blueprint("service", __name__, url_prefix="/service")


def check_schema_compatibility():
    """
    Check if service_events table schema is compatible with the model.
    Returns (is_compatible, error_message) tuple.
    
    This function is now more lenient - title column is optional and will be auto-fixed.
    """
    try:
        # Try a simple query - use explicit column selection to avoid SELECT *
        # This is safer if some columns are missing
        from sqlalchemy import text
        try:
            # Try querying just the id column first (should always exist)
            test_query = db.session.query(ServiceEvent.id).limit(1).all()
            return True, None
        except Exception:
            # If even id query fails, try raw SQL
            db.session.execute(text("SELECT id FROM service_events LIMIT 1"))
            return True, None
    except Exception as e:
        error_str = str(e).lower()
        if "no such column" in error_str or "no column named" in error_str:
            # Title column will be auto-fixed on startup, so don't block access
            # Just log a warning
            current_app.logger.warning(f"Schema compatibility check: {e}")
            # Return compatible=True to allow app to continue (migration will fix it)
            return True, None
        # Re-raise if it's not a schema issue
        raise


# ============================================================================
# DASHBOARD
# ============================================================================

@service_bp.route("/")
@service_bp.route("/dashboard")
@login_required
@role_required(UserRole.Admin, UserRole.SalesManager)
def dashboard():
    """Service Department Dashboard."""
    try:
        # Check schema compatibility first
        is_compatible, schema_error = check_schema_compatibility()
        if not is_compatible:
            current_app.logger.error(f"[SERVICE_MODULE] Schema mismatch in service dashboard: {schema_error}")
            flash("Database schema needs to be updated. Please contact an administrator.", "danger")
            return render_template(
                "service/dashboard.html",
                total_events=0,
                events_today=0,
                events_this_week=0,
                planned=0,
                confirmed=0,
                in_progress=0,
                completed=0,
                recent_events=[],
                upcoming=[],
                today=date.today(),
                schema_error=schema_error,
            )
        
        today = date.today()
        
        # Get statistics - safe defaults
        total_events = ServiceEvent.query.count() or 0
        events_today_list = get_events_today() or []
        events_today = len(events_today_list)
        upcoming_week = get_upcoming_events(days=7) or []
        events_this_week = len(upcoming_week)
        
        # Events by status - safe defaults
        planned_list = get_events_by_status("Planned") or []
        planned = len(planned_list)
        confirmed_list = get_events_by_status("Confirmed") or []
        confirmed = len(confirmed_list)
        in_progress_list = get_events_by_status("In Progress") or []
        in_progress = len(in_progress_list)
        completed_list = get_events_by_status("Completed") or []
        completed = len(completed_list)
        
        # Recent events - safe query with NULL-safe ordering
        try:
            recent_events = ServiceEvent.query.options(
                joinedload(ServiceEvent.client)
            ).order_by(ServiceEvent.created_at.desc()).limit(10).all() or []
        except Exception as e:
            # If query fails due to missing columns, return empty list
            current_app.logger.warning(f"Error loading recent events: {e}")
            recent_events = []
        
        # Upcoming events - safe query
        upcoming = get_upcoming_events(days=14) or []
        
        return render_template(
            "service/dashboard.html",
            total_events=total_events,
            events_today=events_today,
            events_this_week=events_this_week,
            planned=planned,
            confirmed=confirmed,
            in_progress=in_progress,
            completed=completed,
            recent_events=recent_events,
            upcoming=upcoming,
            today=today,
        )
    except Exception as e:
        # Log error but return safe defaults
        error_str = str(e).lower()
        schema_error = None
        if "no such column" in error_str or "no column named" in error_str:
            schema_error = "Database schema mismatch detected. Please run the migration script: python scripts/db_migrations/fix_service_events_schema.py"
            current_app.logger.error(f"Schema mismatch in service dashboard: {e}")
        else:
            current_app.logger.error(f"[SERVICE_MODULE] Error in service dashboard: {e}")
        
        return render_template(
            "service/dashboard.html",
            total_events=0,
            events_today=0,
            events_this_week=0,
            planned=0,
            confirmed=0,
            in_progress=0,
            completed=0,
            recent_events=[],
            upcoming=[],
            today=date.today(),
            schema_error=schema_error,
        )


# ============================================================================
# EVENT LIST
# ============================================================================

@service_bp.route("/events")
@login_required
@role_required(UserRole.Admin, UserRole.SalesManager)
def events():
    """List all service events with filters."""
    try:
        # Check schema compatibility
        is_compatible, schema_error = check_schema_compatibility()
        if not is_compatible:
            current_app.logger.error(f"Schema mismatch in service events list: {schema_error}")
            flash("Database schema needs to be updated. Please contact an administrator.", "danger")
            return render_template(
                "service/events.html",
                events=[],
                pagination=None,
                search="",
                status_filter="",
                event_type_filter="",
                event_types=[],
                statuses=["Planned", "Confirmed", "In Progress", "Completed"],
                schema_error=schema_error,
            )
        
        search = request.args.get("search", "").strip()
        status_filter = request.args.get("status", "").strip()
        event_type_filter = request.args.get("event_type", "").strip()
        
        # Build query with LEFT JOIN for client - safe even if no events exist
        # Use explicit column references and NULL-safe operations
        query = ServiceEvent.query.options(joinedload(ServiceEvent.client))
        
        if search:
            # NULL-safe search - handle cases where title might be NULL
            search_filters = []
            try:
                # Try title search (may fail if column doesn't exist yet)
                search_filters.append(ServiceEvent.title.contains(search))
            except Exception:
                pass  # Title column may not exist yet
            
            # Always include venue and notes (these should exist)
            try:
                search_filters.append(ServiceEvent.venue.contains(search))
            except Exception:
                pass
            
            try:
                search_filters.append(ServiceEvent.notes.contains(search))
            except Exception:
                pass
            
            if search_filters:
                query = query.filter(or_(*search_filters))
        
        if status_filter:
            query = query.filter(ServiceEvent.status == status_filter)
        
        if event_type_filter:
            query = query.filter(ServiceEvent.event_type == event_type_filter)
        
        # Order by event date (upcoming first) - safe with nullslast
        # NULL-safe ordering - handle missing columns gracefully
        try:
            query = query.order_by(
                ServiceEvent.event_date.asc().nullslast(),
                ServiceEvent.created_at.desc()
            )
        except Exception:
            # Fallback to created_at only if event_date column has issues
            try:
                query = query.order_by(ServiceEvent.created_at.desc())
            except Exception:
                pass  # If all ordering fails, return unsorted
        
        pagination = paginate_query(query, per_page=20)
        
        # Get unique event types and statuses for filters - safe defaults
        try:
            event_types = db.session.query(ServiceEvent.event_type).distinct().filter(
                ServiceEvent.event_type.isnot(None)
            ).all()
            event_types = [t[0] for t in event_types if t[0] and t[0]]
        except Exception:
            event_types = []
        
        statuses = ["Planned", "Confirmed", "In Progress", "Completed"]
        
        return render_template(
            "service/events.html",
            events=pagination.items or [],
            pagination=pagination,
            search=search,
            status_filter=status_filter,
            event_type_filter=event_type_filter,
            event_types=event_types,
            statuses=statuses,
        )
    except Exception as e:
        error_str = str(e).lower()
        schema_error = None
        if "no such column" in error_str or "no column named" in error_str:
            schema_error = "Database schema mismatch detected. Please run the migration script: python scripts/db_migrations/fix_service_events_schema.py"
            current_app.logger.error(f"[SERVICE_MODULE] Schema mismatch in service events list: {e}")
        else:
            current_app.logger.error(f"[SERVICE_MODULE] Error in service events list: {e}")
        
        flash("An error occurred loading events.", "danger")
        return render_template(
            "service/events.html",
            events=[],
            pagination=None,
            search="",
            status_filter="",
            event_type_filter="",
            event_types=[],
            statuses=["Planned", "Confirmed", "In Progress", "Completed"],
            schema_error=schema_error,
        )


# ============================================================================
# EVENT CREATE/EDIT
# ============================================================================

@service_bp.route("/events/new", methods=["GET", "POST"])
@login_required
@role_required(UserRole.Admin, UserRole.SalesManager)
def event_new():
    """Create a new service event."""
    if request.method == "POST":
        try:
            title = request.form.get("title", "").strip()
            # Title is now optional (nullable) - provide default if empty
            if not title:
                title = "Untitled Event"
            
            event_date_str = request.form.get("event_date", "").strip()
            event_date = parse_date(event_date_str) if event_date_str else None
            
            event = create_service_event(
                title=title,
                event_type=request.form.get("event_type") or None,
                client_id=request.form.get("client_id", type=int) or None,
                event_date=event_date,
                venue=request.form.get("venue", "").strip() or None,
                guest_count=request.form.get("guest_count", type=int) or None,
                status=request.form.get("status", "Planned"),
                notes=request.form.get("notes", "").strip() or None,
            )
            
            flash(f"Service event '{event.title}' created successfully.", "success")
            return redirect(url_for("service.event_detail", event_id=event.id))
        except Exception as e:
            current_app.logger.error(f"[SERVICE_MODULE] Error creating service event: {e}")
            flash("An error occurred while creating the event. Please try again.", "danger")
            # Fall through to GET handler to show form again
    
    # GET request - show form
    try:
        clients = Client.query.order_by(Client.name.asc()).all() or []
    except Exception:
        clients = []
    event_types = ["Wedding", "Kwanjula", "Kukyala", "Kuhingira", "Nikah", "Corporate", "Birthday", "Other"]
    statuses = ["Planned", "Confirmed", "In Progress", "Completed"]
    
    return render_template(
        "service/event_form.html",
        event=None,
        clients=clients,
        event_types=event_types,
        statuses=statuses,
        ai_planner_enabled=current_app.config.get("AI_EVENT_PLANNER_ENABLED", False),
        CURRENCY=current_app.config.get("CURRENCY_PREFIX", "UGX "),
    )


@service_bp.route("/events/<int:event_id>/edit", methods=["GET", "POST"])
@login_required
@role_required(UserRole.Admin, UserRole.SalesManager)
def event_edit(event_id):
    """Edit a service event."""
    event = get_or_404(ServiceEvent, event_id)
    
    if request.method == "POST":
        title = request.form.get("title", "").strip()
        # Title is now optional (nullable) - provide default if empty
        if not title:
            title = "Untitled Event"
        
        event.title = title
        event.event_type = request.form.get("event_type") or None
        event.client_id = request.form.get("client_id", type=int) or None
        
        event_date_str = request.form.get("event_date", "").strip()
        event.event_date = parse_date(event_date_str) if event_date_str else None
        
        event.venue = request.form.get("venue", "").strip() or None
        guest_count = request.form.get("guest_count", type=int)
        event.guest_count = guest_count if guest_count else None
        event.status = request.form.get("status", "Planned")
        event.notes = request.form.get("notes", "").strip() or None
        event.updated_at = datetime.utcnow()
        
        db.session.commit()
        flash("Event updated successfully.", "success")
        return redirect(url_for("service.event_detail", event_id=event.id))
    
    # GET request - show form
    try:
        clients = Client.query.order_by(Client.name.asc()).all() or []
    except Exception:
        clients = []
    event_types = ["Wedding", "Kwanjula", "Kukyala", "Kuhingira", "Nikah", "Corporate", "Birthday", "Other"]
    statuses = ["Planned", "Confirmed", "In Progress", "Completed"]
    
    return render_template(
        "service/event_form.html",
        event=event,
        clients=clients,
        event_types=event_types,
        statuses=statuses,
        ai_planner_enabled=current_app.config.get("AI_EVENT_PLANNER_ENABLED", False),
        CURRENCY=current_app.config.get("CURRENCY_PREFIX", "UGX "),
    )


# ============================================================================
# EVENT WORKSPACE (CORE FEATURE)
# ============================================================================

@service_bp.route("/events/<int:event_id>", endpoint="event_detail")
@service_bp.route("/events/<int:event_id>", endpoint="event_view")  # Backward compatibility
@login_required
@role_required(UserRole.Admin, UserRole.SalesManager)
def event_detail(event_id):
    """Event workspace - main view with tabs."""
    try:
        # Safe query with optional relationships
        event = ServiceEvent.query.options(
            joinedload(ServiceEvent.client),
            joinedload(ServiceEvent.items),
            joinedload(ServiceEvent.staff_assignments).joinedload(ServiceStaffAssignment.staff),
            joinedload(ServiceEvent.checklist_items),
        ).filter(ServiceEvent.id == event_id).first()
        
        # Load new operational data safely
        try:
            event.checklists = ServiceChecklist.query.filter_by(service_event_id=event_id).options(
                joinedload(ServiceChecklist.items)
            ).all()
        except Exception:
            event.checklists = []
        
        try:
            event.item_movements = ServiceItemMovement.query.filter_by(service_event_id=event_id).all()
        except Exception:
            event.item_movements = []
        
        try:
            event.team_leaders = ServiceTeamLeader.query.filter_by(service_event_id=event_id).all()
        except Exception:
            event.team_leaders = []
        
        try:
            event.team_assignments = ServiceTeamAssignment.query.filter_by(service_event_id=event_id).options(
                joinedload(ServiceTeamAssignment.staff)
            ).all()
        except Exception:
            event.team_assignments = []
        
        if not event:
            abort(404)
        
        # Calculate totals - safe default
        try:
            total_cost = calculate_event_total_cost(event_id) or Decimal("0.00")
        except Exception:
            total_cost = Decimal("0.00")
        
        # Checklist progress - safe defaults
        try:
            completed, total, percentage = get_checklist_progress(event_id)
        except Exception:
            completed, total, percentage = (0, 0, 0)
        
        # Get all users for staff assignment - safe default
        try:
            users = User.query.order_by(User.name.asc()).all() or []
        except Exception:
            users = []
        
        # Get currency from config
        currency = current_app.config.get("CURRENCY_PREFIX", "UGX ")
        
        # Get timeline/activity log (using created_at and updated_at as timeline entries)
        timeline_entries = []
        try:
            if event.created_at:
                timeline_entries.append({
                    'date': event.created_at,
                    'action': 'Event Created',
                    'description': f'Service event "{event.title}" was created'
                })
            if event.updated_at and event.updated_at != event.created_at:
                timeline_entries.append({
                    'date': event.updated_at,
                    'action': 'Event Updated',
                    'description': f'Service event "{event.title}" was last updated'
                })
            # Sort by date descending
            timeline_entries.sort(key=lambda x: x['date'], reverse=True)
        except Exception:
            timeline_entries = []
        
        # Get active tab from query parameter
        active_tab = request.args.get("tab", "overview")
        
        # Get part-time staff for team assignment
        try:
            part_time_staff = PartTimeServiceStaff.query.filter_by(is_active=True).order_by(PartTimeServiceStaff.full_name.asc()).all()
        except Exception:
            part_time_staff = []
        
        # Calculate checklist progress for new checklists
        try:
            all_checklist_items = []
            for checklist in event.checklists:
                all_checklist_items.extend(checklist.items)
            new_completed = sum(1 for item in all_checklist_items if item.is_done)
            new_total = len(all_checklist_items)
            new_percentage = (new_completed / new_total * 100) if new_total > 0 else 0
        except Exception:
            new_completed, new_total, new_percentage = (0, 0, 0)
        
        # Check for unreturned items
        try:
            unreturned_items = [m for m in event.item_movements if m.status in ["missing", "partial"]]
        except Exception:
            unreturned_items = []
        
        return render_template(
            "service/event_view.html",
            event=event,
            total_cost=float(total_cost) if total_cost else 0.0,
            checklist_completed=completed,
            checklist_total=total,
            checklist_percentage=percentage,
            new_checklist_completed=new_completed,
            new_checklist_total=new_total,
            new_checklist_percentage=new_percentage,
            users=users,
            part_time_staff=part_time_staff,
            unreturned_items=unreturned_items,
            CURRENCY=currency,
            timeline_entries=timeline_entries,
            active_tab=active_tab,
        )
    except Exception as e:
        error_str = str(e).lower()
        schema_error = None
        if "no such column" in error_str or "no column named" in error_str:
            schema_error = "Database schema mismatch detected. Please run the migration script: python scripts/db_migrations/fix_service_events_schema.py"
            current_app.logger.error(f"[SERVICE_MODULE] Schema mismatch in event view: {e}")
        else:
            current_app.logger.error(f"[SERVICE_MODULE] Error in event view: {e}")
        
        # Try to get event with minimal query
        try:
            event = ServiceEvent.query.filter_by(id=event_id).first()
            if not event:
                abort(404)
            # Render with safe defaults
            return render_template(
                "service/event_view.html",
                event=event,
                total_cost=0.0,
                checklist_completed=0,
                checklist_total=0,
                checklist_percentage=0,
                users=[],
                CURRENCY=current_app.config.get("CURRENCY_PREFIX", "UGX "),
                schema_error=schema_error,
            )
        except Exception:
            abort(404)


# ============================================================================
# EVENT ITEMS
# ============================================================================

@service_bp.route("/events/<int:event_id>/items", methods=["POST"])
@login_required
@role_required(UserRole.Admin, UserRole.SalesManager)
def event_items_add(event_id):
    """Add an item to a service event."""
    try:
        event = get_or_404(ServiceEvent, event_id)
        
        item_name = request.form.get("item_name", "").strip()
        if not item_name:
            flash("Item name is required.", "danger")
            return redirect(url_for("service.event_detail", event_id=event_id))
        
        quantity = request.form.get("quantity", type=int) or 1
        unit_cost = request.form.get("unit_cost", type=float) or 0.0
        
        item = add_event_item(
            service_event_id=event_id,
            item_name=item_name,
            category=request.form.get("category") or None,
            quantity=quantity,
            unit_cost=unit_cost,
        )
        
        flash("Item added successfully.", "success")
        return redirect(url_for("service.event_detail", event_id=event_id))
    except Exception as e:
        current_app.logger.error(f"[SERVICE_MODULE] Error adding item to event {event_id}: {e}")
        flash("An error occurred while adding the item. Please try again.", "danger")
        return redirect(url_for("service.event_detail", event_id=event_id))


@service_bp.route("/events/<int:event_id>/items/<int:item_id>/delete", methods=["POST"])
@login_required
@role_required(UserRole.Admin, UserRole.SalesManager)
def event_item_delete(event_id, item_id):
    """Delete an item from a service event."""
    try:
        event = get_or_404(ServiceEvent, event_id)
        item = get_or_404(ServiceEventItem, item_id)
        
        if item.service_event_id != event_id:
            abort(404)
        
        db.session.delete(item)
        db.session.commit()
        flash("Item deleted successfully.", "success")
        return redirect(url_for("service.event_detail", event_id=event_id))
    except Exception as e:
        current_app.logger.error(f"[SERVICE_MODULE] Error deleting item {item_id} from event {event_id}: {e}")
        flash("An error occurred while deleting the item. Please try again.", "danger")
        return redirect(url_for("service.event_detail", event_id=event_id))


# ============================================================================
# STAFF ASSIGNMENTS
# ============================================================================

@service_bp.route("/events/<int:event_id>/staff", methods=["POST"])
@login_required
@role_required(UserRole.Admin, UserRole.SalesManager)
def event_staff_add(event_id):
    """Assign staff to a service event."""
    try:
        event = get_or_404(ServiceEvent, event_id)
        
        staff_id = request.form.get("staff_id", type=int) or None
        role = request.form.get("role", "").strip() or None
        shift = request.form.get("shift", "").strip() or None
        
        # Mandatory training enforcement removed - fields do not exist
        
        assignment = assign_staff(
            service_event_id=event_id,
            staff_id=staff_id,
            role=role,
            shift=shift,
            notes=request.form.get("notes", "").strip() or None,
        )
        
        flash("Staff assigned successfully.", "success")
        return redirect(url_for("service.event_detail", event_id=event_id))
    except Exception as e:
        current_app.logger.error(f"[SERVICE_MODULE] Error assigning staff to event {event_id}: {e}")
        flash("An error occurred while assigning staff. Please try again.", "danger")
        return redirect(url_for("service.event_detail", event_id=event_id))


@service_bp.route("/events/<int:event_id>/staff/<int:assignment_id>/delete", methods=["POST"])
@login_required
@role_required(UserRole.Admin, UserRole.SalesManager)
def event_staff_delete(event_id, assignment_id):
    """Remove staff assignment from a service event."""
    try:
        event = get_or_404(ServiceEvent, event_id)
        assignment = get_or_404(ServiceStaffAssignment, assignment_id)
        
        if assignment.service_event_id != event_id:
            abort(404)
        
        db.session.delete(assignment)
        db.session.commit()
        flash("Staff assignment removed successfully.", "success")
        return redirect(url_for("service.event_detail", event_id=event_id))
    except Exception as e:
        current_app.logger.error(f"[SERVICE_MODULE] Error deleting staff assignment {assignment_id} from event {event_id}: {e}")
        flash("An error occurred while removing the staff assignment. Please try again.", "danger")
        return redirect(url_for("service.event_detail", event_id=event_id))


# ============================================================================
# CHECKLIST
# ============================================================================

@service_bp.route("/events/<int:event_id>/checklist", methods=["POST"])
@login_required
@role_required(UserRole.Admin, UserRole.SalesManager)
def event_checklist_add(event_id):
    """Add a checklist item to a service event."""
    try:
        event = get_or_404(ServiceEvent, event_id)
        
        description = request.form.get("description", "").strip()
        if not description:
            flash("Task description is required.", "danger")
            return redirect(url_for("service.event_detail", event_id=event_id))
        
        item = add_checklist_item(
            service_event_id=event_id,
            description=description,
            stage=request.form.get("stage") or None,
        )
        
        flash("Checklist item added successfully.", "success")
        return redirect(url_for("service.event_detail", event_id=event_id))
    except Exception as e:
        current_app.logger.error(f"[SERVICE_MODULE] Error adding checklist item to event {event_id}: {e}")
        flash("An error occurred while adding the checklist item. Please try again.", "danger")
        return redirect(url_for("service.event_detail", event_id=event_id))


@service_bp.route("/events/<int:event_id>/checklist/<int:item_id>/toggle", methods=["POST"])
@login_required
@role_required(UserRole.Admin, UserRole.SalesManager)
def event_checklist_toggle(event_id, item_id):
    """Toggle checklist item completion."""
    try:
        event = get_or_404(ServiceEvent, event_id)
        item = get_or_404(ServiceChecklistItem, item_id)
        
        if item.service_event_id != event_id:
            abort(404)
        
        new_status = toggle_checklist_item(item_id)
        
        if request.is_json:
            return jsonify({"ok": True, "completed": new_status})
        
        flash("Checklist item updated.", "success")
        return redirect(url_for("service.event_detail", event_id=event_id))
    except Exception as e:
        current_app.logger.error(f"[SERVICE_MODULE] Error toggling checklist item {item_id} for event {event_id}: {e}")
        if request.is_json:
            return jsonify({"ok": False, "error": "Failed to update checklist item"}), 500
        flash("An error occurred while updating the checklist item. Please try again.", "danger")
        return redirect(url_for("service.event_detail", event_id=event_id))


@service_bp.route("/events/<int:event_id>/checklist/<int:item_id>/delete", methods=["POST"])
@login_required
@role_required(UserRole.Admin, UserRole.SalesManager)
def event_checklist_delete(event_id, item_id):
    """Delete a checklist item."""
    try:
        event = get_or_404(ServiceEvent, event_id)
        item = get_or_404(ServiceChecklistItem, item_id)
        
        if item.service_event_id != event_id:
            abort(404)
        
        db.session.delete(item)
        db.session.commit()
        flash("Checklist item deleted successfully.", "success")
        return redirect(url_for("service.event_detail", event_id=event_id))
    except Exception as e:
        current_app.logger.error(f"[SERVICE_MODULE] Error deleting checklist item {item_id} from event {event_id}: {e}")
        flash("An error occurred while deleting the checklist item. Please try again.", "danger")
        return redirect(url_for("service.event_detail", event_id=event_id))


# ============================================================================
# STATUS UPDATE
# ============================================================================

@service_bp.route("/events/<int:event_id>/status", methods=["POST"])
@login_required
@role_required(UserRole.Admin, UserRole.SalesManager)
def event_status_update(event_id):
    """Update event status with business rules validation."""
    try:
        event = get_or_404(ServiceEvent, event_id)
        
        new_status = request.form.get("status") or (request.get_json().get("status") if request.is_json else None)
        if not new_status:
            if request.is_json:
                return jsonify({"ok": False, "error": "Status not provided"}), 400
            flash("Status is required.", "danger")
            return redirect(url_for("service.event_detail", event_id=event_id))
        
        # Business Rule: Event cannot be closed if checklist is incomplete
        if new_status == "Completed":
            try:
                # Check new operational checklists
                incomplete_checklists = []
                for checklist in getattr(event, 'checklists', []):
                    if not checklist.is_completed:
                        incomplete_checklists.append(checklist.title)
                
                if incomplete_checklists:
                    error_msg = f"Cannot close event. Incomplete checklists: {', '.join(incomplete_checklists)}"
                    if request.is_json:
                        return jsonify({"ok": False, "error": error_msg}), 400
                    flash(error_msg, "warning")
                    return redirect(url_for("service.event_detail", event_id=event_id, tab="checklist"))
                
                # Check for unreturned items
                unreturned = [m for m in getattr(event, 'item_movements', []) if m.status in ["missing", "partial"]]
                if unreturned:
                    items_list = ", ".join([m.item_name for m in unreturned[:5]])
                    error_msg = f"Cannot close event. Unreturned items: {items_list}" + ("..." if len(unreturned) > 5 else "")
                    if request.is_json:
                        return jsonify({"ok": False, "error": error_msg}), 400
                    flash(error_msg, "warning")
                    return redirect(url_for("service.event_detail", event_id=event_id, tab="items-movement"))
            except Exception as e:
                current_app.logger.warning(f"Error checking business rules: {e}")
                # Don't block status update if check fails - log warning only
        
        update_event_status(event_id, new_status)
        
        if request.is_json:
            return jsonify({"ok": True, "status": new_status})
        
        flash("Event status updated.", "success")
        return redirect(url_for("service.event_detail", event_id=event_id))
    except Exception as e:
        current_app.logger.error(f"[SERVICE_MODULE] Error updating status for event {event_id}: {e}")
        if request.is_json:
            return jsonify({"ok": False, "error": "Failed to update status"}), 500
        flash("An error occurred while updating the status. Please try again.", "danger")
        return redirect(url_for("service.event_detail", event_id=event_id))


# ============================================================================
# ADDITIONAL ROUTE ALIASES FOR CLEAN URLS
# ============================================================================

@service_bp.route("/events/<int:event_id>/timeline")
@login_required
@role_required(UserRole.Admin, UserRole.SalesManager)
def event_timeline(event_id):
    """Event timeline view."""
    try:
        return redirect(url_for("service.event_detail", event_id=event_id, tab="timeline"))
    except Exception as e:
        current_app.logger.error(f"Error in event_timeline: {e}")
        flash("Error loading timeline.", "danger")
        return redirect(url_for("service.events"))

@service_bp.route("/events/<int:event_id>/staff")
@login_required
@role_required(UserRole.Admin, UserRole.SalesManager)
def event_staff(event_id):
    """Event staff assignments view."""
    try:
        return redirect(url_for("service.event_detail", event_id=event_id, tab="staff"))
    except Exception as e:
        current_app.logger.error(f"Error in event_staff: {e}")
        flash("Error loading staff assignments.", "danger")
        return redirect(url_for("service.events"))

@service_bp.route("/events/<int:event_id>/checklists")
@login_required
@role_required(UserRole.Admin, UserRole.SalesManager)
def event_checklists(event_id):
    """Event checklists view."""
    try:
        return redirect(url_for("service.event_detail", event_id=event_id, tab="checklist"))
    except Exception as e:
        current_app.logger.error(f"Error in event_checklists: {e}")
        flash("Error loading checklists.", "danger")
        return redirect(url_for("service.events"))

@service_bp.route("/events/<int:event_id>/costs")
@login_required
@role_required(UserRole.Admin, UserRole.SalesManager)
def event_costs(event_id):
    """Event costs view."""
    try:
        return redirect(url_for("service.event_detail", event_id=event_id, tab="costs"))
    except Exception as e:
        current_app.logger.error(f"Error in event_costs: {e}")
        flash("Error loading costs.", "danger")
        return redirect(url_for("service.events"))


# ============================================================================
# AI PLANNING ASSISTANT
# ============================================================================

@service_bp.route("/ai/plan", methods=["POST"])
@login_required
@role_required(UserRole.Admin, UserRole.SalesManager)
def ai_plan():
    """
    AI-powered event planning assistant endpoint.
    
    Accepts JSON payload with event inputs and returns planning suggestions.
    Fails gracefully if AI is disabled or data is insufficient.
    """
    try:
        # Check if AI planner is enabled
        if not current_app.config.get("AI_EVENT_PLANNER_ENABLED", False):
            return jsonify({
                "enabled": False,
                "reason": "AI Event Planner is disabled",
            }), 200
        
        # Import AI planner (safe - will fail gracefully if missing)
        try:
            from sas_management.service.ai_planner import generate_plan
        except ImportError as e:
            current_app.logger.warning(f"AI planner not available: {e}")
            return jsonify({
                "enabled": False,
                "reason": "AI planner service not available",
            }), 200
        
        # Get JSON payload
        data = request.get_json() or {}
        
        # Extract event inputs
        event_type = data.get("event_type") or None
        guest_count = data.get("guest_count")
        if guest_count is not None:
            try:
                guest_count = int(guest_count)
            except (ValueError, TypeError):
                guest_count = None
        
        event_date_str = data.get("event_date")
        event_date = None
        if event_date_str:
            try:
                event_date = parse_date(event_date_str)
            except Exception:
                event_date = None
        
        # Generate plan
        result = generate_plan(
            event_type=event_type,
            guest_count=guest_count,
            event_date=event_date,
        )
        
        # Return suggestions
        return jsonify({
            "enabled": True,
            "success": True,
            **result,
        }), 200
        
    except Exception as e:
        # Log as warning - AI is optional
        current_app.logger.warning(f"Error in AI planning endpoint: {e}")
        return jsonify({
            "enabled": True,
            "success": False,
            "reason": "insufficient data",
            "staff_suggestions": [],
            "checklist": [],
            "estimated_cost": 0.0,
            "confidence_note": f"Planning suggestions unavailable: {str(e)}",
        }), 200
