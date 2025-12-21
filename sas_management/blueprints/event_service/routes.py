"""
Event Service Blueprint - Routes
"""
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from datetime import datetime, timedelta, date
from sas_management.models import db, UserRole
from sas_management.utils import role_required
from sas_management.blueprints.event_service.models import (
    EventServiceOrder,
    EventCosting,
    EventStaffAssignment,
    EventVendor,
    EventReport,
)
from sas_management.models import (
    Event,
    EventChecklist,
    EventChecklistItem,
    ChecklistItem,
    EventMessageThread,
    EventTimeline,
    EventDocument,
    EventMessage,
)
from sas_management.blueprints.event_service.services import (
    create_event,
    add_service_order,
    add_costing,
    assign_staff,
    add_vendor,
    add_timeline_item,
    add_document,
    add_checklist_item,
    add_message,
    generate_report as generate_report_service,
)
from sas_management.blueprints.event_service.analytics import (
    get_event_statistics,
    get_revenue_analytics,
    get_cost_analytics,
    get_staff_utilization,
)
from sas_management.blueprints.event_service.reports import (
    generate_event_summary_report,
    generate_financial_report,
)

# Create blueprint
event_service_bp = Blueprint("event_service", __name__, url_prefix="/event-service")


# ============================================================================
# TIMELINE ROUTES (PRIMARY - MUST BE AT TOP)
# ============================================================================

@event_service_bp.route("/timeline")
@login_required
def timeline_index():
    """Timeline selector page - shows all events for timeline selection."""
    events = (
        Event.query
        .order_by(Event.date.desc())
        .all()
    )
    return render_template(
        "event_service/timeline_index.html",
        events=events
    )


@event_service_bp.route("/checklists")
@login_required
def service_checklists():
    """Operational checklists index - shows all checklists across all events."""
    events = Event.query.order_by(Event.id.desc()).all()
    
    checklists = EventChecklist.query.all()
    
    items = ChecklistItem.query.all()
    
    return render_template(
        "event_service/checklists.html",
        events=events,
        checklists=checklists,
        items=items
    )


@event_service_bp.route("/messages")
@login_required
def service_messages():
    """Operational messages index - shows all messages across all events."""
    event_id = request.args.get("event_id", type=int)
    
    events = Event.query.order_by(Event.id.desc()).all()
    
    # Load threads
    threads_query = EventMessageThread.query
    if event_id:
        threads_query = threads_query.filter_by(event_id=event_id)
    threads = threads_query.order_by(EventMessageThread.updated_at.desc()).all()
    
    # Load messages - filter by thread_ids if event_id is specified
    messages_query = EventMessage.query
    if event_id:
        thread_ids = [t.id for t in threads]
        if thread_ids:
            messages_query = messages_query.filter(EventMessage.thread_id.in_(thread_ids))
        else:
            messages_query = messages_query.filter(False)  # No threads = no messages
    messages = messages_query.order_by(EventMessage.timestamp.desc()).all()
    
    return render_template(
        "event_service/messages.html",
        events=events,
        messages=messages,
        threads=threads,
        selected_event_id=event_id
    )


@event_service_bp.route("/messages/send", methods=["POST"])
@login_required
def send_service_message():
    """Send a new message to an event."""
    from datetime import timezone
    
    event_id = request.form.get("event_id", type=int)
    content = request.form.get("content", "").strip()
    
    if not content or not event_id:
        flash("Event ID and message content are required", "danger")
        return redirect(url_for("event_service.service_messages"))
    
    # Get or create thread for this event
    thread = EventMessageThread.query.filter_by(event_id=event_id).first()
    if not thread:
        thread = EventMessageThread(event_id=event_id)
        db.session.add(thread)
        db.session.flush()
    
    # Create message
    message = EventMessage(
        thread_id=thread.id,
        sender_id=current_user.id,
        message=content,
        timestamp=datetime.now(timezone.utc)
    )
    db.session.add(message)
    
    # Update thread timestamp
    thread.updated_at = datetime.now(timezone.utc)
    
    db.session.commit()
    flash("Message sent successfully", "success")
    return redirect(url_for("event_service.service_messages", event_id=event_id))


@event_service_bp.route("/reports")
@login_required
def service_reports():
    """Operational service delivery reports."""
    today = date.today()
    events = Event.query.order_by(Event.date.desc()).all()
    
    completed_events = Event.query.filter_by(status="Completed").count()
    in_progress_events = Event.query.filter_by(status="In Progress").count()
    delayed_events = Event.query.filter(Event.date < today, Event.status != "Completed").count()
    
    return render_template(
        "event_service/reports.html",
        events=events,
        completed_events=completed_events,
        in_progress_events=in_progress_events,
        delayed_events=delayed_events,
        today=today
    )


@event_service_bp.route("/analytics")
@login_required
def service_analytics():
    """Service performance analytics."""
    total_events = Event.query.count()
    completed = Event.query.filter_by(status="Completed").count()
    in_progress = Event.query.filter_by(status="In Progress").count()
    planned = Event.query.filter_by(status="Planned").count()
    
    completion_rate = (
        round((completed / total_events) * 100, 1)
        if total_events else 0
    )
    
    return render_template(
        "event_service/analytics.html",
        total_events=total_events,
        completed=completed,
        in_progress=in_progress,
        planned=planned,
        completion_rate=completion_rate
    )


@event_service_bp.route("/checklists/item/<int:item_id>/toggle")
@login_required
def toggle_checklist_item(item_id):
    """Toggle checklist item completion status."""
    from datetime import timezone
    item = ChecklistItem.query.get_or_404(item_id)
    item.is_completed = not item.is_completed
    item.completed_at = datetime.now(timezone.utc) if item.is_completed else None
    item.completed_by = current_user.id if current_user.is_authenticated else None
    db.session.commit()
    flash("Checklist item updated", "success")
    return redirect(request.referrer or url_for("event_service.service_checklists"))


@event_service_bp.route("/checklists/item/add", methods=["POST"])
@login_required
def add_checklist_item():
    """Add a new checklist item."""
    checklist_id = request.form.get("checklist_id", type=int)
    description = request.form.get("description", "").strip()
    
    if not checklist_id or not description:
        flash("Checklist ID and description are required", "danger")
        return redirect(request.referrer or url_for("event_service.service_checklists"))
    
    checklist = EventChecklist.query.get_or_404(checklist_id)
    
    # Get max order_index for this checklist
    max_order = db.session.query(db.func.max(ChecklistItem.order_index)).filter_by(checklist_id=checklist_id).scalar() or 0
    
    item = ChecklistItem(
        checklist_id=checklist_id,
        description=description,
        order_index=max_order + 1,
        is_completed=False
    )
    db.session.add(item)
    db.session.commit()
    flash("Checklist item added", "success")
    return redirect(request.referrer or url_for("event_service.service_checklists"))


@event_service_bp.route("/checklists/create", methods=["POST"])
@login_required
def create_checklist():
    """Create a new checklist for an event."""
    event_id = request.form.get("event_id", type=int)
    checklist_type = request.form.get("checklist_type", "").strip()
    title = request.form.get("title", "").strip()
    
    if not event_id or not checklist_type or not title:
        flash("Event ID, checklist type, and title are required", "danger")
        return redirect(request.referrer or url_for("event_service.service_checklists"))
    
    event = Event.query.get_or_404(event_id)
    
    checklist = EventChecklist(
        event_id=event_id,
        checklist_type=checklist_type,
        title=title,
        created_by=current_user.id if current_user.is_authenticated else None
    )
    db.session.add(checklist)
    db.session.commit()
    flash("Checklist created", "success")
    return redirect(request.referrer or url_for("event_service.service_checklists"))


@event_service_bp.route("/documents")
@login_required
def documents_index():
    """Operational documents index - shows all documents across all events."""
    from collections import defaultdict
    
    from sqlalchemy.orm import joinedload
    
    events = Event.query.order_by(Event.date.desc()).all()
    documents = EventDocument.query.options(joinedload(EventDocument.event), joinedload(EventDocument.user)).join(Event).order_by(EventDocument.uploaded_at.desc()).all()
    
    # Document categories
    document_categories = ["Run Sheet", "Floor Plan", "Safety", "Photos", "Sign-off", "Other"]
    
    # Helper function to derive category from document title/file_type
    def get_category(doc):
        title_lower = doc.title.lower()
        if "run" in title_lower or "sheet" in title_lower:
            return "Run Sheet"
        elif "floor" in title_lower or "plan" in title_lower:
            return "Floor Plan"
        elif "safety" in title_lower or "haccp" in title_lower:
            return "Safety"
        elif "photo" in title_lower or "image" in title_lower or doc.file_type and "image" in doc.file_type.lower():
            return "Photos"
        elif "sign" in title_lower or "approval" in title_lower:
            return "Sign-off"
        else:
            return "Other"
    
    # Group documents by event and compute statistics
    documents_by_event = {}
    
    for event in events:
        event_docs = [d for d in documents if d.event_id == event.id]
        
        total_documents = len(event_docs)
        categories_present = set()
        last_uploaded_at = None
        
        for doc in event_docs:
            category = get_category(doc)
            categories_present.add(category)
            if not last_uploaded_at or (doc.uploaded_at and doc.uploaded_at > last_uploaded_at):
                last_uploaded_at = doc.uploaded_at
        
        # Required documents: Run Sheet, Floor Plan, Safety, Sign-off
        required_categories = {"Run Sheet", "Floor Plan", "Safety", "Sign-off"}
        required_documents_missing = not required_categories.issubset(categories_present)
        
        documents_by_event[event.id] = {
            "total_documents": total_documents,
            "required_documents_missing": required_documents_missing,
            "last_uploaded_at": last_uploaded_at,
            "categories_present": list(categories_present),
            "documents": event_docs
        }
    
    return render_template(
        "event_service/documents.html",
        events=events,
        documents=documents,
        documents_by_event=documents_by_event,
        document_categories=document_categories
    )


# ============================================================================
# DASHBOARD / OVERVIEW
# ============================================================================

# ============================================================================
# LEGACY ROUTES - DISABLED (Using core Event model only)
# ============================================================================

# @event_service_bp.route("/")
# @event_service_bp.route("/dashboard")
# @login_required
# def dashboard():
#     """Event Service Dashboard."""
#     stats = get_event_statistics()
#     # Use Event.date or fallback to event_date for ordering
#     events = Event.query.order_by(
#         db.func.coalesce(Event.date, Event.event_date).desc()
#     ).limit(10).all()
#     return render_template("event_service/dashboard.html", stats=stats, recent_events=events)


# @event_service_bp.route("/overview")
# @login_required
# def services_overview():
#     """Services Overview - Execution Control Center."""
#     # DISABLED - Legacy service_events route
#     from datetime import datetime, timedelta, date
#     
#     # Query active/upcoming events (not completed, date >= today or recent past)
#     today = datetime.utcnow().date()
#     cutoff_date = today - timedelta(days=7)  # Include events from last 7 days
#     
#     # Use Event.date or fallback to event_date
#     active_events = Event.query.filter(
#         Event.status != "Completed"
#     ).filter(
#         db.func.coalesce(Event.date, Event.event_date) >= cutoff_date
#     ).order_by(db.func.coalesce(Event.date, Event.event_date).asc()).all()
#     
#     service_events = []
#     
#     for event in active_events:
#         event_id = event.id
#         # Get event date (prefer date, fallback to event_date)
#         event_date = event.date if event.date else (event.event_date if event.event_date else today)
#         if isinstance(event_date, datetime):
#             event_date = event_date.date()
#         
#         # Query timeline items
#         timeline_items = EventTimeline.query.filter_by(event_id=event_id).all()
#         
#         # Query checklist items
#         checklist_items = EventChecklistItem.query.filter_by(event_id=event_id).all()
#         
#         # Query documents
#         documents = EventDocument.query.filter_by(event_id=event_id).all()
#         
#         # Query messages via EventMessageThread
#         message_thread = EventMessageThread.query.filter_by(event_id=event_id).first()
#         messages = []
#         if message_thread:
#             messages = EventMessage.query.filter_by(thread_id=message_thread.id).all()
#         
#         # Compute service_status
#         service_status = "Not Started"
#         if timeline_items:
#             # Check if any timeline phase has started (completed or due_date passed)
#             started_phases = [t for t in timeline_items if t.completed or (t.due_date and t.due_date <= today)]
#             if started_phases:
#                 # Check if service phase is active (Execution phase)
#                 active_phases = [t for t in timeline_items if t.phase == "Execution" and not t.completed]
#                 if active_phases:
#                     service_status = "In Progress"
#                 else:
#                     # Check if service end is marked
#                     completed_phases = [t for t in timeline_items if t.completed]
#                     if len(completed_phases) == len(timeline_items):
#                         service_status = "Completed"
#                     else:
#                         service_status = "Setup"
#         
#         # Compute checklist_completion_percent
#         total_items = len(checklist_items)
#         completed_items = len([item for item in checklist_items if item.completed])
#         checklist_completion_percent = int((completed_items / total_items * 100)) if total_items > 0 else 0
#         
#         # Compute overdue_checklist_items_count
#         # Since EventChecklistItem doesn't have due_date, consider items overdue if:
#         # - Not completed AND event_date is within 3 days or passed
#         three_days_from_now = today + timedelta(days=3)
#         overdue_items = [
#             item for item in checklist_items 
#             if not item.completed and event_date <= three_days_from_now
#         ]
#         overdue_checklist_items_count = len(overdue_items)
#         
#         # Compute missing_required_documents_count
#         # Since there's no required flag, we'll check if there are any documents at all
#         # For now, we'll consider it a risk if there are no documents and event is approaching
#         missing_required_documents_count = 0
#         if len(documents) == 0 and event_date <= today + timedelta(days=7):
#             missing_required_documents_count = 1  # Flag as missing if no docs and event soon
#         
#         # Compute timeline_delay_flag
#         timeline_delay_flag = False
#         for timeline_item in timeline_items:
#             if timeline_item.due_date and timeline_item.due_date < today and not timeline_item.completed:
#                 timeline_delay_flag = True
#                 break
#         
#         # Compute last_activity_timestamp
#         last_activity_timestamp = None
#         timestamps = []
#         
#         # Get latest checklist completion
#         for item in checklist_items:
#             if item.completed_at:
#                 timestamps.append(item.completed_at)
#         
#         # Get latest timeline update
#         for timeline_item in timeline_items:
#             if timeline_item.completed_at:
#                 timestamps.append(timeline_item.completed_at)
#             if timeline_item.created_at:
#                 timestamps.append(timeline_item.created_at)
#         
#         # Get latest message
#         for message in messages:
#             if message.timestamp:
#                 timestamps.append(message.timestamp)
#         
#         # Get latest document upload
#         for doc in documents:
#             if doc.uploaded_at:
#                 timestamps.append(doc.uploaded_at)
#         
#         if timestamps:
#             last_activity_timestamp = max(timestamps)
#         
#         # Compute service_readiness_score (0-100)
#         # Based on: checklist completion (40%), documents (20%), timeline adherence (30%), overdue items (10% penalty)
#         readiness_score = 0
#         
#         # Checklist completion (40 points max)
#         readiness_score += (checklist_completion_percent / 100) * 40
#         
#         # Documents (20 points max) - if documents exist, give full points
#         if len(documents) > 0:
#             readiness_score += 20
#         elif event_date > today + timedelta(days=7):
#             readiness_score += 10  # Partial points if event is far away
#         
#         # Timeline adherence (30 points max) - no delays = full points
#         if not timeline_delay_flag:
#             readiness_score += 30
#         else:
#             # Penalty based on number of delayed items
#             delayed_count = len([t for t in timeline_items if t.due_date and t.due_date < today and not t.completed])
#             penalty = min(delayed_count * 5, 30)  # Max 30 point penalty
#             readiness_score += max(0, 30 - penalty)
#         
#         # Overdue items penalty (10 points max penalty)
#         if overdue_checklist_items_count > 0:
#             penalty = min(overdue_checklist_items_count * 2, 10)
#             readiness_score = max(0, readiness_score - penalty)
#         
#         readiness_score = min(100, max(0, int(readiness_score)))
#         
#         # Get venue name from venue_obj relationship
#         venue_name = event.venue_obj.name if event.venue_obj else None
#         
#         service_events.append({
#             "event": event,
#             "service_status": service_status,
#             "checklist_completion_percent": checklist_completion_percent,
#             "overdue_checklist_items_count": overdue_checklist_items_count,
#             "missing_required_documents_count": missing_required_documents_count,
#             "timeline_delay_flag": timeline_delay_flag,
#             "last_activity_timestamp": last_activity_timestamp,
#             "service_readiness_score": readiness_score,
#             "event_date": event_date,
#             "venue_name": venue_name
#         })
#     
#     # Compute KPI summary
#     total_active = len(service_events)
#     events_in_progress = len([e for e in service_events if e["service_status"] == "In Progress"])
#     events_at_risk = len([e for e in service_events if e["timeline_delay_flag"] or e["overdue_checklist_items_count"] > 0 or e["service_readiness_score"] < 60])
#     events_completed = len([e for e in service_events if e["service_status"] == "Completed"])
#     
#     return render_template(
#         "event_service/services_overview.html",
#         service_events=service_events,
#         total_active=total_active,
#         events_in_progress=events_in_progress,
#         events_at_risk=events_at_risk,
#         events_completed=events_completed
#     )


# ============================================================================
# EVENTS
# ============================================================================

@event_service_bp.route("/events")
@login_required
def events_list():
    """Service-Focused All Events - Execution View."""
    from sqlalchemy import or_
    
    # Get query parameters for filtering and search
    service_status_filter = request.args.get("service_status", "").strip()
    execution_phase_filter = request.args.get("execution_phase", "").strip()
    readiness_filter = request.args.get("readiness", "").strip()
    search_query = request.args.get("search", "").strip()
    date_from = request.args.get("date_from", "").strip()
    date_to = request.args.get("date_to", "").strip()
    
    # Base query - get all events
    query = Event.query
    
    # Apply search filter
    if search_query:
        search_term = f"%{search_query}%"
        # Event has venue_obj relationship, so we need to join or search differently
        # For now, search by title and ID, venue search would require join
        query = query.filter(
            or_(
                Event.title.ilike(search_term),
                Event.id.cast(db.String).ilike(search_term)  # Search by ID as reference
            )
        )
    
    # Apply date range filter
    if date_from:
        try:
            date_from_obj = datetime.strptime(date_from, "%Y-%m-%d").date()
            query = query.filter(db.func.coalesce(Event.date, Event.event_date) >= date_from_obj)
        except ValueError:
            pass
    
    if date_to:
        try:
            date_to_obj = datetime.strptime(date_to, "%Y-%m-%d").date()
            query = query.filter(db.func.coalesce(Event.date, Event.event_date) <= date_to_obj)
        except ValueError:
            pass
    
    # Get all events (we'll filter by service_status and readiness after computing metrics)
    events = query.order_by(db.func.coalesce(Event.date, Event.event_date).desc()).all()
    
    today = datetime.utcnow().date()
    service_events = []
    
    for event in events:
        event_id = event.id
        # Get event date (prefer date, fallback to event_date)
        event_date = event.date if event.date else (event.event_date if event.event_date else today)
        if isinstance(event_date, datetime):
            event_date = event_date.date()
        
        # Query timeline items
        timeline_items = EventTimeline.query.filter_by(event_id=event_id).all()
        
        # Query checklists and checklist items
        checklists = EventChecklist.query.filter_by(event_id=event_id).all()
        checklist_items = EventChecklistItem.query.filter_by(event_id=event_id).all()
        
        # Query documents
        documents = EventDocument.query.filter_by(event_id=event_id).all()
        
        # Compute service_status
        service_status = "Not Started"
        execution_phase = None
        
        if timeline_items:
            # Check if any timeline phase has started
            started_phases = [t for t in timeline_items if t.completed or (t.due_date and t.due_date <= today)]
            if started_phases:
                # Find current execution phase
                active_phases = [t for t in timeline_items if not t.completed]
                if active_phases:
                    # Get the earliest active phase
                    earliest_active = min(active_phases, key=lambda x: x.due_date if x.due_date else date.max)
                    execution_phase = earliest_active.phase
                    
                    if execution_phase == "Execution":
                        service_status = "In Progress"
                    else:
                        service_status = "Setup"
                else:
                    # All phases completed
                    service_status = "Completed"
                    execution_phase = "Post-Event"
            else:
                execution_phase = "Planning"
        
        # Compute checklist_completion_percent
        total_items = len(checklist_items)
        completed_items = len([item for item in checklist_items if item.completed])
        checklist_completion_percent = int((completed_items / total_items * 100)) if total_items > 0 else 0
        
        # Compute overdue_tasks_count
        # Count checklist items not completed and timeline items overdue
        overdue_checklist = [
            item for item in checklist_items 
            if not item.completed and event_date <= today + timedelta(days=3)
        ]
        overdue_timeline = [
            t for t in timeline_items 
            if t.due_date and t.due_date < today and not t.completed
        ]
        overdue_tasks_count = len(overdue_checklist) + len(overdue_timeline)
        
        # Compute missing_required_documents_count
        missing_required_documents_count = 0
        if len(documents) == 0 and event_date <= today + timedelta(days=7):
            missing_required_documents_count = 1
        
        # Compute service_ready_flag
        # Ready if: checklist >= 80%, no overdue tasks, no missing docs, no timeline delays
        timeline_delay = any(
            t.due_date and t.due_date < today and not t.completed 
            for t in timeline_items
        )
        service_ready_flag = (
            checklist_completion_percent >= 80 and
            overdue_tasks_count == 0 and
            missing_required_documents_count == 0 and
            not timeline_delay
        )
        
        # Compute service_completed_timestamp
        service_completed_timestamp = None
        if service_status == "Completed" and timeline_items:
            completed_phases = [t for t in timeline_items if t.completed and t.completed_at]
            if completed_phases:
                # Get the latest completion timestamp
                service_completed_timestamp = max(t.completed_at for t in completed_phases)
        
        # Compute post_event_review_status
        post_event_review_status = "Pending"
        if service_status == "Completed":
            # Check if there's a Post-Event phase that's completed
            post_event_phases = [t for t in timeline_items if t.phase == "Post-Event"]
            if post_event_phases and all(t.completed for t in post_event_phases):
                post_event_review_status = "Done"
        
        # Determine readiness for filtering
        readiness = "Ready" if service_ready_flag else "At Risk"
        
        # Apply filters
        if service_status_filter and service_status != service_status_filter:
            continue
        
        if execution_phase_filter and execution_phase != execution_phase_filter:
            continue
        
        if readiness_filter:
            if readiness_filter == "Ready" and not service_ready_flag:
                continue
            if readiness_filter == "At Risk" and service_ready_flag:
                continue
        
        # Get venue name from venue_obj relationship
        venue_name = event.venue_obj.name if event.venue_obj else None
        
        service_events.append({
            "event": event,
            "service_status": service_status,
            "execution_phase": execution_phase or "N/A",
            "checklist_completion_percent": checklist_completion_percent,
            "overdue_tasks_count": overdue_tasks_count,
            "missing_required_documents_count": missing_required_documents_count,
            "service_ready_flag": service_ready_flag,
            "service_completed_timestamp": service_completed_timestamp,
            "post_event_review_status": post_event_review_status,
            "event_date": event_date,
            "readiness": readiness,
            "venue_name": venue_name
        })
    
#     return render_template(
#         "event_service/all_events.html",
#         events=service_events,
#         service_status_filter=service_status_filter,
#         execution_phase_filter=execution_phase_filter,
#         readiness_filter=readiness_filter,
#         search_query=search_query,
#         date_from=date_from,
#         date_to=date_to
#     )


@event_service_bp.route("/events/new", methods=["GET", "POST"])
@login_required
@role_required(UserRole.Admin, UserRole.SalesManager)
def event_create():
    """Create a new event."""
    if request.method == "POST":
        try:
            event_date = datetime.strptime(request.form.get("event_date"), "%Y-%m-%dT%H:%M")
            event = create_event(
                title=request.form.get("title"),
                description=request.form.get("description"),
                event_date=event_date,
                client_id=request.form.get("client_id") or None,
                venue=request.form.get("venue"),
                guest_count=int(request.form.get("guest_count", 0)),
                created_by=current_user.id
            )
            flash("Event created successfully", "success")
            return redirect(url_for("event_service.event_view", event_id=event.id))
        except Exception as e:
            flash(f"Error creating event: {str(e)}", "danger")
    
    return render_template("event_service/event_form.html")


@event_service_bp.route("/events/<int:event_id>")
@login_required
def event_view(event_id):
    """View event details."""
    event = Event.query.get_or_404(event_id)
    return render_template("event_service/event_view.html", event=event)


@event_service_bp.route("/events/<int:event_id>/edit", methods=["GET", "POST"])
@login_required
@role_required(UserRole.Admin, UserRole.SalesManager)
def event_edit(event_id):
    """Edit an event."""
    event = Event.query.get_or_404(event_id)
    
    if request.method == "POST":
        try:
            event.title = request.form.get("title")
            event.description = request.form.get("description")
            event.event_date = datetime.strptime(request.form.get("event_date"), "%Y-%m-%dT%H:%M")
            event.venue = request.form.get("venue")
            event.guest_count = int(request.form.get("guest_count", 0))
            event.status = request.form.get("status")
            event.updated_at = datetime.utcnow()
            db.session.commit()
            flash("Event updated successfully", "success")
            return redirect(url_for("event_service.event_view", event_id=event.id))
        except Exception as e:
            flash(f"Error updating event: {str(e)}", "danger")
    
    return render_template("event_service/event_form.html", event=event)


# ============================================================================
# SERVICE ORDERS
# ============================================================================

@event_service_bp.route("/events/<int:event_id>/orders")
@login_required
def service_orders(event_id):
    """View service orders for an event."""
    event = Event.query.get_or_404(event_id)
    orders = EventServiceOrder.query.filter_by(event_id=event_id).all()
    return render_template("event_service/service_orders.html", event=event, orders=orders)


@event_service_bp.route("/events/<int:event_id>/orders/new", methods=["POST"])
@login_required
@role_required(UserRole.Admin, UserRole.SalesManager)
def service_order_add(event_id):
    """Add a service order."""
    try:
        add_service_order(
            event_id=event_id,
            service_name=request.form.get("service_name"),
            quantity=int(request.form.get("quantity", 1)),
            unit_price=float(request.form.get("unit_price", 0)),
            notes=request.form.get("notes")
        )
        flash("Service order added successfully", "success")
    except Exception as e:
        flash(f"Error adding service order: {str(e)}", "danger")
    
    return redirect(url_for("event_service.service_orders", event_id=event_id))


# ============================================================================
# COSTING & QUOTATIONS
# ============================================================================

@event_service_bp.route("/events/<int:event_id>/costing")
@login_required
def costing(event_id):
    """View costing and quotations for an event."""
    event = Event.query.get_or_404(event_id)
    costings = EventCosting.query.filter_by(event_id=event_id).all()
    return render_template("event_service/costing.html", event=event, costings=costings)


@event_service_bp.route("/events/<int:event_id>/costing/new", methods=["POST"])
@login_required
@role_required(UserRole.Admin, UserRole.SalesManager)
def costing_add(event_id):
    """Add a costing item."""
    try:
        add_costing(
            event_id=event_id,
            item_name=request.form.get("item_name"),
            category=request.form.get("category"),
            quantity=int(request.form.get("quantity", 1)),
            unit_cost=float(request.form.get("unit_cost", 0)),
            is_quoted=request.form.get("is_quoted") == "on"
        )
        flash("Costing item added successfully", "success")
    except Exception as e:
        flash(f"Error adding costing item: {str(e)}", "danger")
    
    return redirect(url_for("event_service.costing", event_id=event_id))


# ============================================================================
# STAFF ASSIGNMENTS
# ============================================================================

@event_service_bp.route("/events/<int:event_id>/staff")
@login_required
def staff_assignments(event_id):
    """View staff assignments for an event."""
    event = Event.query.get_or_404(event_id)
    assignments = EventStaffAssignment.query.filter_by(event_id=event_id).all()
    return render_template("event_service/staff_assignments.html", event=event, assignments=assignments)


@event_service_bp.route("/events/<int:event_id>/staff/new", methods=["POST"])
@login_required
@role_required(UserRole.Admin, UserRole.SalesManager)
def staff_assignment_add(event_id):
    """Add a staff assignment."""
    try:
        start_time = datetime.strptime(request.form.get("start_time"), "%Y-%m-%dT%H:%M") if request.form.get("start_time") else None
        end_time = datetime.strptime(request.form.get("end_time"), "%Y-%m-%dT%H:%M") if request.form.get("end_time") else None
        
        assign_staff(
            event_id=event_id,
            staff_id=int(request.form.get("staff_id")),
            role=request.form.get("role"),
            start_time=start_time,
            end_time=end_time,
            hourly_rate=float(request.form.get("hourly_rate", 0)) if request.form.get("hourly_rate") else None
        )
        flash("Staff assigned successfully", "success")
    except Exception as e:
        flash(f"Error assigning staff: {str(e)}", "danger")
    
    return redirect(url_for("event_service.staff_assignments", event_id=event_id))


# ============================================================================
# VENDORS
# ============================================================================

@event_service_bp.route("/events/<int:event_id>/vendors")
@login_required
def vendors(event_id):
    """View vendors for an event."""
    event = Event.query.get_or_404(event_id)
    vendor_list = EventVendor.query.filter_by(event_id=event_id).all()
    return render_template("event_service/vendors.html", event=event, vendors=vendor_list)


@event_service_bp.route("/events/<int:event_id>/vendors/new", methods=["POST"])
@login_required
@role_required(UserRole.Admin, UserRole.SalesManager)
def vendor_add(event_id):
    """Add a vendor."""
    try:
        add_vendor(
            event_id=event_id,
            vendor_name=request.form.get("vendor_name"),
            vendor_contact=request.form.get("vendor_contact"),
            service_provided=request.form.get("service_provided"),
            cost=float(request.form.get("cost", 0))
        )
        flash("Vendor added successfully", "success")
    except Exception as e:
        flash(f"Error adding vendor: {str(e)}", "danger")
    
    return redirect(url_for("event_service.vendors", event_id=event_id))


# ============================================================================
# TIMELINE - OPERATIONAL EXECUTION VIEW
# ============================================================================

@event_service_bp.route("/timeline/<int:event_id>")
@login_required
def service_timeline(event_id):
    """Operational Timeline - Service Execution View (PRIMARY ROUTE)."""
    event = Event.query.get_or_404(event_id)
    phases = EventTimeline.query.filter_by(event_id=event_id)\
                                 .order_by(EventTimeline.due_date.asc().nullslast())\
                                 .all()
    
    today = datetime.utcnow().date()
    timeline_phases = []
    
    # Track which phase is currently active
    active_phase_id = None
    previous_phase_completed = True
    
    for idx, item in enumerate(phases):
        # Determine phase_status
        phase_status = "Pending"
        delay_reason = None
        planned_time = item.due_date
        actual_time = item.completed_at.date() if item.completed_at else None
        
        if item.completed:
            phase_status = "Completed"
            # Check if there was a delay (completed after due date)
            if item.due_date and item.completed_at:
                if item.completed_at.date() > item.due_date:
                    phase_status = "Delayed"
                    if "DELAY:" in item.description:
                        delay_reason = item.description.split("DELAY:")[-1].strip()
        else:
            # Phase not completed - determine status
            is_overdue = item.due_date and item.due_date < today
            is_next_phase = previous_phase_completed or idx == 0
            
            if is_overdue:
                phase_status = "Delayed"
                if "DELAY:" in item.description:
                    delay_reason = item.description.split("DELAY:")[-1].strip()
                if is_next_phase:
                    active_phase_id = item.id
            elif is_next_phase:
                phase_status = "Active"
                active_phase_id = item.id
            else:
                phase_status = "Pending"
        
        # Calculate time variance (days)
        time_variance = None
        if planned_time and actual_time:
            time_variance = (actual_time - planned_time).days
        elif planned_time and phase_status in ["Delayed", "Active"]:
            time_variance = (today - planned_time).days
        
        # Check cascade delay
        cascade_delay = False
        if idx > 0 and timeline_phases:
            prev_phase = timeline_phases[-1]
            if prev_phase["phase_status"] == "Delayed" and phase_status == "Pending":
                cascade_delay = True
        
        timeline_phases.append({
            "item": item,
            "phase_status": phase_status,
            "planned_time": planned_time,
            "actual_time": actual_time,
            "time_variance": time_variance,
            "delay_reason": delay_reason,
            "is_active": (item.id == active_phase_id),
            "is_overdue": (item.due_date and item.due_date < today and not item.completed),
            "cascade_delay": cascade_delay
        })
        
        previous_phase_completed = item.completed
    
    return render_template(
        "event_service/timeline.html",
        event=event,
        timeline_phases=timeline_phases
    )


# Legacy route - redirects to primary timeline route
@event_service_bp.route("/events/<int:event_id>/timeline")
@login_required
def timeline(event_id):
    """Legacy route - redirects to primary timeline route."""
    return redirect(url_for("event_service.service_timeline", event_id=event_id))


@event_service_bp.route("/events/<int:event_id>/timeline/<int:phase_id>/start", methods=["POST"])
@login_required
def timeline_phase_start(event_id, phase_id):
    """Mark a timeline phase as started (execution action)."""
    phase = EventTimeline.query.get_or_404(phase_id)
    
    # Verify phase belongs to this event
    if phase.event_id != event_id:
        flash("Phase does not belong to this event", "danger")
        return redirect(url_for("event_service.service_timeline", event_id=event_id))
    
    # Mark as started (phase is considered started when created_at exists)
    # Since we can't modify schema, we'll use completed_at=None and ensure created_at exists
    if not phase.completed:
        # Phase is now active
        flash(f"Phase '{phase.phase}' marked as started", "success")
    else:
        flash("Phase is already completed", "warning")
    
    db.session.commit()
    return redirect(url_for("event_service.service_timeline", event_id=event_id))


@event_service_bp.route("/events/<int:event_id>/timeline/<int:phase_id>/complete", methods=["POST"])
@login_required
def timeline_phase_complete(event_id, phase_id):
    """Mark a timeline phase as completed (execution action)."""
    phase = EventTimeline.query.get_or_404(phase_id)
    
    # Verify phase belongs to this event
    if phase.event_id != event_id:
        flash("Phase does not belong to this event", "danger")
        return redirect(url_for("event_service.service_timeline", event_id=event_id))
    
    # Mark as completed
    phase.completed = True
    phase.completed_at = datetime.utcnow()
    db.session.commit()
    
    flash(f"Phase '{phase.phase}' marked as completed", "success")
    return redirect(url_for("event_service.service_timeline", event_id=event_id))


@event_service_bp.route("/events/<int:event_id>/timeline/<int:phase_id>/delay", methods=["POST"])
@login_required
def timeline_phase_delay(event_id, phase_id):
    """Log a delay reason for a timeline phase (execution action)."""
    phase = EventTimeline.query.get_or_404(phase_id)
    delay_reason = request.form.get("delay_reason", "").strip()
    
    # Verify phase belongs to this event
    if phase.event_id != event_id:
        flash("Phase does not belong to this event", "danger")
        return redirect(url_for("event_service.service_timeline", event_id=event_id))
    
    # Store delay reason in description (since we can't modify schema)
    # Append delay reason with DELAY: prefix for parsing
    if delay_reason:
        # Remove existing DELAY: entry if present
        desc = phase.description
        if "DELAY:" in desc:
            desc = desc.split("DELAY:")[0].strip()
        
        # Append new delay reason
        phase.description = f"{desc}\n\nDELAY: {delay_reason}"
        db.session.commit()
        flash(f"Delay reason logged for phase '{phase.phase}'", "success")
    else:
        flash("Delay reason cannot be empty", "danger")
    
    return redirect(url_for("event_service.service_timeline", event_id=event_id))


# ============================================================================
# DOCUMENTS
# ============================================================================

@event_service_bp.route("/events/<int:event_id>/documents")
@login_required
def documents(event_id):
    """View documents for an event."""
    event = Event.query.get_or_404(event_id)
    document_list = EventDocument.query.filter_by(event_id=event_id).all()
    return render_template("event_service/documents.html", event=event, documents=document_list)


@event_service_bp.route("/events/<int:event_id>/documents/upload", methods=["POST"])
@login_required
@role_required(UserRole.Admin, UserRole.SalesManager)
def document_upload(event_id):
    """Upload a document."""
    try:
        if "file" not in request.files:
            flash("No file selected", "danger")
            return redirect(url_for("event_service.documents", event_id=event_id))
        
        file = request.files["file"]
        if file.filename == "":
            flash("No file selected", "danger")
            return redirect(url_for("event_service.documents", event_id=event_id))
        
        # Save file (simplified - in production, use secure_filename and proper storage)
        import os
        from werkzeug.utils import secure_filename
        from flask import current_app
        
        upload_folder = os.path.join(current_app.root_path, "static", "event_service", "documents")
        os.makedirs(upload_folder, exist_ok=True)
        
        filename = secure_filename(file.filename)
        file_path = os.path.join(upload_folder, filename)
        file.save(file_path)
        
        # Store relative path for template access
        relative_path = os.path.join("static", "event_service", "documents", filename)
        
        add_document(
            event_id=event_id,
            filename=filename,
            file_path=relative_path,
            file_type=file.content_type,
            file_size=os.path.getsize(file_path),
            description=request.form.get("description"),
            uploaded_by=current_user.id
        )
        flash("Document uploaded successfully", "success")
    except Exception as e:
        flash(f"Error uploading document: {str(e)}", "danger")
    
    return redirect(url_for("event_service.documents", event_id=event_id))


# ============================================================================
# CHECKLISTS
# ============================================================================

@event_service_bp.route("/events/<int:event_id>/checklists")
@login_required
def checklists(event_id):
    """View checklists for an event using existing EventChecklist models."""
    # Get the Event for context
    event = Event.query.get_or_404(event_id)
    
    # Query EventChecklist filtered by event_id
    # EventChecklist references "event.id" (main Event model)
    # We'll query EventChecklist and EventChecklistItem
    checklists = EventChecklist.query.filter_by(event_id=event_id).all()
    
    checklist_data = []
    
    # Process each EventChecklist
    for checklist in checklists:
        # Get EventChecklistItem for this event
        items = EventChecklistItem.query.filter_by(event_id=event_id).all()
        total = len(items)
        completed = len([i for i in items if i.completed])
        progress = int((completed / total) * 100) if total else 0
        
        checklist_data.append({
            "checklist": checklist,
            "items": items,
            "progress": progress,
            "total": total,
            "completed": completed
        })
    
    # If no EventChecklist exists, show EventChecklistItem directly
    if not checklists:
        items = EventChecklistItem.query.filter_by(event_id=event_id).all()
        total = len(items)
        completed = len([i for i in items if i.completed])
        progress = int((completed / total) * 100) if total else 0
        
        checklist_data.append({
            "checklist": None,
            "items": items,
            "progress": progress,
            "total": total,
            "completed": completed
        })
    
    return render_template(
        "event_service/checklists.html",
        event=event,
        checklist_data=checklist_data
    )


@event_service_bp.route("/events/<int:event_id>/checklists/new", methods=["POST"])
@login_required
@role_required(UserRole.Admin, UserRole.SalesManager)
def checklist_add(event_id):
    """Add a checklist item."""
    try:
        due_date = datetime.strptime(request.form.get("due_date"), "%Y-%m-%dT%H:%M") if request.form.get("due_date") else None
        add_checklist_item(
            event_id=event_id,
            item_name=request.form.get("item_name"),
            description=request.form.get("description"),
            category=request.form.get("category"),
            due_date=due_date
        )
        flash("Checklist item added successfully", "success")
    except Exception as e:
        flash(f"Error adding checklist item: {str(e)}", "danger")
    
    return redirect(url_for("event_service.checklists", event_id=event_id))


@event_service_bp.route("/events/<int:event_id>/checklists/<int:item_id>/toggle", methods=["POST"])
@login_required
def checklist_toggle(event_id, item_id):
    """Toggle checklist item completion using EventChecklistItem."""
    item = EventChecklistItem.query.get_or_404(item_id)
    # Verify it belongs to this event
    if item.event_id != event_id:
        flash("Item does not belong to this event", "danger")
        return redirect(url_for("event_service.checklists", event_id=event_id))
    
    item.completed = not item.completed
    if item.completed:
        item.completed_at = datetime.utcnow()
    else:
        item.completed_at = None
    db.session.commit()
    flash("Checklist item updated", "success")
    return redirect(url_for("event_service.checklists", event_id=event_id))


# ============================================================================
# MESSAGES
# ============================================================================

@event_service_bp.route("/events/<int:event_id>/messages")
@login_required
def messages(event_id):
    """View messages for an event."""
    event = Event.query.get_or_404(event_id)
    message_list = EventMessage.query.filter_by(event_id=event_id).order_by(EventMessage.created_at.desc()).all()
    return render_template("event_service/messages.html", event=event, messages=message_list)


@event_service_bp.route("/events/<int:event_id>/messages/new", methods=["POST"])
@login_required
def message_add(event_id):
    """Add a message."""
    try:
        add_message(
            event_id=event_id,
            sender_id=current_user.id,
            message=request.form.get("message"),
            message_type=request.form.get("message_type", "General")
        )
        flash("Message sent successfully", "success")
    except Exception as e:
        flash(f"Error sending message: {str(e)}", "danger")
    
    return redirect(url_for("event_service.messages", event_id=event_id))


# ============================================================================
# REPORTS
# ============================================================================

@event_service_bp.route("/events/<int:event_id>/reports")
@login_required
def reports(event_id):
    """View reports for an event."""
    event = Event.query.get_or_404(event_id)
    report_list = EventReport.query.filter_by(event_id=event_id).order_by(EventReport.generated_at.desc()).all()
    return render_template("event_service/reports.html", event=event, reports=report_list)


@event_service_bp.route("/events/<int:event_id>/reports/generate", methods=["POST"])
@login_required
@role_required(UserRole.Admin, UserRole.SalesManager)
def report_generate(event_id):
    """Generate a report."""
    try:
        report_type = request.form.get("report_type")
        title = request.form.get("title")
        
        if report_type == "summary":
            report_data = generate_event_summary_report(event_id)
            content = f"Summary report for {report_data['event'].title}"
        elif report_type == "financial":
            report_data = generate_financial_report(event_id)
            content = f"Financial report: Revenue: {report_data['revenue']}, Profit: {report_data['profit']}"
        else:
            content = f"Report: {title}"
        
        generate_report_service(
            event_id=event_id,
            report_type=report_type,
            title=title,
            content=content,
            generated_by=current_user.id
        )
        flash("Report generated successfully", "success")
    except Exception as e:
        flash(f"Error generating report: {str(e)}", "danger")
    
    return redirect(url_for("event_service.reports", event_id=event_id))


# ============================================================================
# ANALYTICS
# ============================================================================

@event_service_bp.route("/analytics")
@login_required
@role_required(UserRole.Admin, UserRole.SalesManager)
def analytics():
    """Event Service Analytics Dashboard."""
    stats = get_event_statistics()
    revenue = get_revenue_analytics()
    costs = get_cost_analytics()
    staff_util = get_staff_utilization()
    
    return render_template(
        "event_service/analytics.html",
        stats=stats,
        revenue=revenue,
        costs=costs,
        staff_util=staff_util
    )

