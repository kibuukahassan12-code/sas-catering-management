"""Timeline Planner routes."""
from flask import Blueprint, render_template, request, jsonify, flash, redirect, url_for
from flask_login import login_required, current_user
from datetime import datetime, date, timedelta
import json

from models import db, Timeline, Event, Task, UserRole, TaskStatus
from utils import role_required
from utils.helpers import parse_date

timeline_bp = Blueprint("timeline", __name__, url_prefix="/timeline")

@timeline_bp.route("/edit/<int:event_id>")
@login_required
@role_required(UserRole.Admin, UserRole.SalesManager)
def edit(event_id):
    """Timeline editor."""
    event = Event.query.get_or_404(event_id)
    timeline = Timeline.query.filter_by(event_id=event_id).first()
    return render_template("timeline/timeline_editor.html", event=event, timeline=timeline)

@timeline_bp.route("/save/<int:event_id>", methods=["POST"])
@login_required
@role_required(UserRole.Admin, UserRole.SalesManager)
def save(event_id):
    """Save timeline."""
    try:
        data = request.get_json()
        timeline = Timeline.query.filter_by(event_id=event_id).first()
        
        if timeline:
            timeline.json_timeline = json.dumps(data.get('timeline', []))
        else:
            timeline = Timeline(
                event_id=event_id,
                json_timeline=json.dumps(data.get('timeline', [])),
                created_by=current_user.id
            )
            db.session.add(timeline)
        
        db.session.commit()
        return jsonify({'success': True})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500

@timeline_bp.route("/view/<int:event_id>")
@login_required
def view(event_id):
    """View timeline."""
    event = Event.query.get_or_404(event_id)
    timeline = Timeline.query.filter_by(event_id=event_id).first()
    return render_template("timeline/timeline_view.html", event=event, timeline=timeline)

@timeline_bp.route("/export/<int:event_id>")
@login_required
def export(event_id):
    """Export timeline as PDF."""
    timeline = Timeline.query.filter_by(event_id=event_id).first_or_404()
    # TODO: Implement PDF export
    return jsonify({'success': False, 'error': 'PDF export not yet implemented'})

@timeline_bp.route("/planner")
@login_required
def planner():
    """Comprehensive timeline planner showing all events and tasks with sample data."""
    # Get filter parameters
    start_date_str = request.args.get("start_date", "")
    end_date_str = request.args.get("end_date", "")
    event_type_filter = request.args.get("event_type", "")
    status_filter = request.args.get("status", "")
    view_mode = request.args.get("view", "timeline")  # timeline or calendar
    use_sample = request.args.get("sample", "false") == "true"
    
    # Parse dates
    start_date = parse_date(start_date_str) if start_date_str else date.today() - timedelta(days=30)
    end_date = parse_date(end_date_str) if end_date_str else date.today() + timedelta(days=90)
    
    if use_sample or (Event.query.count() == 0 and Task.query.count() == 0):
        # Generate sample data if requested or if database is empty
        events, tasks = _generate_sample_data(start_date, end_date)
        event_types = ["Wedding", "Corporate", "Birthday", "Conference", "Anniversary"]
        event_statuses = ["Draft", "Confirmed", "In Progress", "Completed", "Cancelled"]
    else:
        # Build event query
        events_query = Event.query.filter(
            Event.event_date >= start_date,
            Event.event_date <= end_date
        )
        
        if event_type_filter:
            events_query = events_query.filter(Event.event_type == event_type_filter)
        
        if status_filter:
            events_query = events_query.filter(Event.status == status_filter)
        
        events = events_query.order_by(Event.event_date.asc()).all()
        
        # Build task query
        tasks_query = Task.query.filter(
            Task.due_date >= start_date,
            Task.due_date <= end_date
        )
        
        if status_filter:
            if status_filter == "Pending":
                tasks_query = tasks_query.filter(Task.status == TaskStatus.Pending)
            elif status_filter == "In Progress":
                tasks_query = tasks_query.filter(Task.status == TaskStatus.InProgress)
            elif status_filter == "Completed":
                tasks_query = tasks_query.filter(Task.status == TaskStatus.Completed)
        
        tasks = tasks_query.order_by(Task.due_date.asc()).all()
        
        # Get unique values for filters
        event_types = db.session.query(Event.event_type).distinct().filter(Event.event_type.isnot(None)).all()
        event_types = [et[0] for et in event_types if et[0]]
        
        event_statuses = db.session.query(Event.status).distinct().all()
        event_statuses = [es[0] for es in event_statuses if es[0]]
    
    return render_template(
        "timeline/planner.html",
        events=events,
        tasks=tasks,
        event_types=event_types,
        event_statuses=event_statuses,
        start_date=start_date_str,
        end_date=end_date_str,
        selected_event_type=event_type_filter,
        selected_status=status_filter,
        view_mode=view_mode,
        use_sample=use_sample,
    )

def _generate_sample_data(start_date, end_date):
    """Generate sample events and tasks for demonstration."""
    from random import choice, randint
    
    # Create simple classes to mimic model objects
    class SampleEvent:
        def __init__(self, **kwargs):
            for key, value in kwargs.items():
                setattr(self, key, value)
    
    class SampleTask:
        def __init__(self, **kwargs):
            for key, value in kwargs.items():
                setattr(self, key, value)
            # Ensure status has a value attribute for consistency
            if hasattr(self.status, 'value'):
                pass
            else:
                # Create a simple status object
                class Status:
                    def __init__(self, val):
                        self.value = val
                if isinstance(self.status, str):
                    self.status = Status(self.status)
    
    class SampleClient:
        def __init__(self, name):
            self.name = name
    
    class SampleUser:
        def __init__(self, email):
            self.email = email
    
    sample_events = []
    sample_tasks = []
    
    event_types = ["Wedding", "Corporate", "Birthday", "Conference", "Anniversary", "Graduation"]
    event_statuses = ["Draft", "Confirmed", "In Progress", "Completed"]
    task_statuses = [TaskStatus.Pending, TaskStatus.InProgress, TaskStatus.Completed]
    venues = ["Grand Ballroom", "Garden Venue", "Conference Center", "Beach Resort", "City Hall", "Hotel Banquet"]
    client_names = ["ABC Corporation", "Smith Family", "Johnson Wedding", "Tech Conference", "University Event"]
    
    # Generate sample events
    current_date = start_date
    event_id = 1
    while current_date <= end_date and len(sample_events) < 20:
        if randint(1, 3) == 1:  # 33% chance of event on this day
            client_obj = SampleClient(choice(client_names)) if randint(1, 2) == 1 else None
            sample_events.append(SampleEvent(
                id=event_id,
                event_name=f"{choice(event_types)} - {choice(client_names)}",
                event_date=current_date,
                event_type=choice(event_types),
                status=choice(event_statuses),
                venue=choice(venues),
                guest_count=randint(50, 500),
                event_time=f"{randint(9, 18):02d}:00",
                client=client_obj,
            ))
            event_id += 1
        current_date += timedelta(days=randint(1, 7))
    
    # Generate sample tasks
    current_date = start_date
    task_id = 1
    task_titles = [
        "Finalize menu selection",
        "Confirm guest count",
        "Book photographer",
        "Arrange transportation",
        "Prepare event materials",
        "Send invitations",
        "Coordinate with vendors",
        "Setup venue",
        "Review contracts",
        "Prepare presentation"
    ]
    
    while current_date <= end_date and len(sample_tasks) < 15:
        if randint(1, 4) == 1:  # 25% chance of task on this day
            user_obj = SampleUser(f"user{randint(1, 3)}@example.com") if randint(1, 2) == 1 else None
            sample_tasks.append(SampleTask(
                id=task_id,
                title=choice(task_titles),
                due_date=current_date,
                status=choice(task_statuses),
                description="Task related to event planning and coordination",
                assigned_user=user_obj,
            ))
            task_id += 1
        current_date += timedelta(days=randint(1, 5))
    
    return sample_events, sample_tasks

@timeline_bp.route("/api/data")
@login_required
def api_data():
    """API endpoint for timeline data (for AJAX updates)."""
    start_date_str = request.args.get("start_date", "")
    end_date_str = request.args.get("end_date", "")
    event_type_filter = request.args.get("event_type", "")
    status_filter = request.args.get("status", "")
    
    start_date = parse_date(start_date_str) if start_date_str else date.today() - timedelta(days=30)
    end_date = parse_date(end_date_str) if end_date_str else date.today() + timedelta(days=90)
    
    # Get events
    events_query = Event.query.filter(
        Event.event_date >= start_date,
        Event.event_date <= end_date
    )
    
    if event_type_filter:
        events_query = events_query.filter(Event.event_type == event_type_filter)
    if status_filter:
        events_query = events_query.filter(Event.status == status_filter)
    
    events = events_query.order_by(Event.event_date.asc()).all()
    
    # Get tasks
    tasks_query = Task.query.filter(
        Task.due_date >= start_date,
        Task.due_date <= end_date
    )
    
    if status_filter:
        if status_filter == "Pending":
            tasks_query = tasks_query.filter(Task.status == TaskStatus.Pending)
        elif status_filter == "In Progress":
            tasks_query = tasks_query.filter(Task.status == TaskStatus.InProgress)
        elif status_filter == "Completed":
            tasks_query = tasks_query.filter(Task.status == TaskStatus.Completed)
    
    tasks = tasks_query.order_by(Task.due_date.asc()).all()
    
    # Format data for JSON response
    events_data = [{
        'id': e.id,
        'title': e.event_name,
        'date': e.event_date.isoformat(),
        'type': 'event',
        'status': e.status,
        'event_type': e.event_type,
        'client': e.client.name if e.client else None,
        'venue': e.venue,
        'guest_count': e.guest_count,
    } for e in events]
    
    tasks_data = [{
        'id': t.id,
        'title': t.title,
        'date': t.due_date.isoformat() if t.due_date else None,
        'type': 'task',
        'status': t.status.value,
        'description': t.description,
        'assigned_to': t.assigned_user.email if t.assigned_user else None,
    } for t in tasks]
    
    return jsonify({
        'success': True,
        'events': events_data,
        'tasks': tasks_data
    })

