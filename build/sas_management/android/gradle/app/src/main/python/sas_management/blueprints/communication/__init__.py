"""Communication Hub Blueprint - Internal messaging, announcements, tasks."""
from datetime import datetime, date
from flask import Blueprint, current_app, flash, jsonify, redirect, render_template, request, send_from_directory, url_for
from flask_login import current_user, login_required
from sqlalchemy.orm import joinedload

from models import (
    db, User, UserRole, Event,
    Announcement, BulletinPost, DirectMessageThread, DirectMessage,
    DepartmentMessage, EventMessageThread, EventMessage, StaffTask
)
from utils import role_required
from services.communication_service import (
    create_announcement, list_announcements, get_announcement,
    add_bulletin_post, get_bulletin,
    get_or_create_thread, send_direct_message, get_thread_messages, get_user_threads,
    post_department_message, get_department_messages,
    get_or_create_event_thread, post_event_message, get_event_thread_messages,
    create_task, update_task_status, list_tasks_for_user, get_task,
    get_upload_folder
)
import os

comm_bp = Blueprint("communication", __name__, url_prefix="/communication")

@comm_bp.route("/dashboard")
@login_required
def dashboard():
    """Communication hub dashboard."""
    try:
        # Get recent announcements
        announcements_result = list_announcements(limit=5)
        recent_announcements = announcements_result.get('announcements', [])
        
        # Get current user tasks
        tasks_result = list_tasks_for_user(current_user.id, status_filter='pending')
        current_tasks = tasks_result.get('tasks', [])[:5]
        
        # Get user's active threads
        threads_result = get_user_threads(current_user.id)
        active_threads = threads_result.get('threads', [])[:5]
        
        # Get recent bulletin posts
        bulletin_result = get_bulletin(limit=5)
        recent_bulletin = bulletin_result.get('posts', [])
        
        return render_template("communication/comm_dashboard.html",
            recent_announcements=recent_announcements,
            current_tasks=current_tasks,
            active_threads=active_threads,
            recent_bulletin=recent_bulletin
        )
    except Exception as e:
        current_app.logger.exception(f"Error loading communication dashboard: {e}")
        return render_template("communication/comm_dashboard.html",
            recent_announcements=[],
            current_tasks=[],
            active_threads=[],
            recent_bulletin=[]
        )

# ============================
# ANNOUNCEMENTS
# ============================

@comm_bp.route("/announcements")
@login_required
def announcements_list():
    """List all announcements."""
    try:
        result = list_announcements()
        announcements = result.get('announcements', [])
        return render_template("communication/announcements.html", announcements=announcements)
    except Exception as e:
        current_app.logger.exception(f"Error loading announcements: {e}")
        return render_template("communication/announcements.html", announcements=[])

@comm_bp.route("/announcement/<int:announcement_id>")
@login_required
def announcement_view(announcement_id):
    """View a specific announcement."""
    try:
        result = get_announcement(announcement_id)
        if not result['success']:
            flash(result.get('error', 'Announcement not found'), "danger")
            return redirect(url_for("communication.announcements_list"))
        
        announcement = result['announcement']
        return render_template("communication/announcement_view.html", announcement=announcement)
    except Exception as e:
        current_app.logger.exception(f"Error viewing announcement: {e}")
        return redirect(url_for("communication.announcements_list"))

@comm_bp.route("/announcement/new", methods=["GET", "POST"])
@login_required
@role_required(UserRole.Admin, UserRole.SalesManager)
def announcement_new():
    """Create a new announcement."""
    if request.method == "POST":
        try:
            data = {
                'title': request.form.get('title', '').strip(),
                'message': request.form.get('message', '').strip(),
                'created_by': current_user.id
            }
            
            image_file = request.files.get('image') if 'image' in request.files else None
            
            if not data['title'] or not data['message']:
                flash("Title and message are required.", "danger")
                return render_template("communication/announcement_form.html")
            
            result = create_announcement(data, image_file)
            
            if result['success']:
                flash("Announcement created successfully!", "success")
                return redirect(url_for("communication.announcement_view", announcement_id=result['announcement'].id))
            else:
                flash(f"Error: {result.get('error', 'Unknown error')}", "danger")
        except Exception as e:
            current_app.logger.exception(f"Error creating announcement: {e}")
    
    return render_template("communication/announcement_form.html")

# ============================
# BULLETIN BOARD
# ============================

@comm_bp.route("/bulletin")
@login_required
def bulletin():
    """Bulletin board."""
    try:
        result = get_bulletin()
        posts = result.get('posts', [])
        return render_template("communication/bulletin.html", posts=posts)
    except Exception as e:
        current_app.logger.exception(f"Error loading bulletin: {e}")
        return render_template("communication/bulletin.html", posts=[])

@comm_bp.route("/bulletin/post", methods=["POST"])
@login_required
def bulletin_post():
    """Post to bulletin board."""
    try:
        message = request.form.get('message', '').strip()
        if not message:
            flash("Message cannot be empty.", "danger")
            return redirect(url_for("communication.bulletin"))
        
        result = add_bulletin_post(message, current_user.id)
        
        if result['success']:
            flash("Posted to bulletin board!", "success")
        else:
            flash(f"Error: {result.get('error', 'Unknown error')}", "danger")
    except Exception as e:
        current_app.logger.exception(f"Error posting to bulletin: {e}")
    
    return redirect(url_for("communication.bulletin"))

# ============================
# DEPARTMENT MESSAGES
# ============================

@comm_bp.route("/department/<department>")
@login_required
def department_messages(department):
    """View department messages."""
    try:
        result = get_department_messages(department)
        messages = result.get('messages', [])
        return render_template("communication/department_messages.html",
            department=department,
            messages=messages
        )
    except Exception as e:
        current_app.logger.exception(f"Error loading department messages: {e}")
        return render_template("communication/department_messages.html",
            department=department,
            messages=[]
        )

@comm_bp.route("/department/<department>/send", methods=["POST"])
@login_required
def department_send(department):
    """Send a department message."""
    try:
        message = request.form.get('message', '').strip()
        if not message:
            flash("Message cannot be empty.", "danger")
            return redirect(url_for("communication.department_messages", department=department))
        
        attachment_file = request.files.get('attachment') if 'attachment' in request.files else None
        
        result = post_department_message(department, message, current_user.id, attachment_file)
        
        if result['success']:
            flash("Message posted!", "success")
        else:
            flash(f"Error: {result.get('error', 'Unknown error')}", "danger")
    except Exception as e:
        current_app.logger.exception(f"Error sending department message: {e}")
    
    return redirect(url_for("communication.department_messages", department=department))

# ============================
# EVENT MESSAGES
# ============================

@comm_bp.route("/messages")
@login_required
def message_threads():
    # Compatibility route so old links don't break
    # Redirect to events list since event_messages requires an event_id
    return redirect(url_for("events.events_list"))

@comm_bp.route("/events/<int:event_id>")
@login_required
def event_messages(event_id):
    """View event message thread."""
    try:
        event = Event.query.get_or_404(event_id)
        
        result = get_or_create_event_thread(event_id)
        if not result['success']:
            flash(f"Error: {result.get('error')}", "danger")
            return redirect(url_for("events.event_view", event_id=event_id))
        
        thread = result['thread']
        messages_result = get_event_thread_messages(thread.id)
        messages = messages_result.get('messages', [])
        
        return render_template("communication/event_messages.html",
            event=event,
            thread=thread,
            messages=messages
        )
    except Exception as e:
        current_app.logger.exception(f"Error loading event messages: {e}")
        return redirect(url_for("events.events_list"))

@comm_bp.route("/events/<int:event_id>/send", methods=["POST"])
@login_required
def event_send(event_id):
    """Send a message to an event thread."""
    try:
        result = get_or_create_event_thread(event_id)
        if not result['success']:
            flash(f"Error: {result.get('error')}", "danger")
            return redirect(url_for("communication.event_messages", event_id=event_id))
        
        thread = result['thread']
        message = request.form.get('message', '').strip()
        
        if not message:
            flash("Message cannot be empty.", "danger")
            return redirect(url_for("communication.event_messages", event_id=event_id))
        
        attachment_file = request.files.get('attachment') if 'attachment' in request.files else None
        
        result = post_event_message(thread.id, current_user.id, message, attachment_file)
        
        if result['success']:
            flash("Message posted!", "success")
        else:
            flash(f"Error: {result.get('error', 'Unknown error')}", "danger")
    except Exception as e:
        current_app.logger.exception(f"Error sending event message: {e}")
    
    return redirect(url_for("communication.event_messages", event_id=event_id))

# ============================
# STAFF TASKS
# ============================

@comm_bp.route("/tasks")
@login_required
def staff_tasks():
    """View staff tasks."""
    try:
        status_filter = request.args.get('status', None)
        
        # Admin can see all tasks, others see only their own
        if current_user.is_super_admin() or current_user.role == UserRole.Admin:
            query = StaffTask.query
            if status_filter:
                query = query.filter_by(status=status_filter)
            tasks = query.order_by(StaffTask.created_at.desc()).all()
        else:
            result = list_tasks_for_user(current_user.id, status_filter)
            tasks = result.get('tasks', [])
        
        return render_template("communication/staff_tasks.html", tasks=tasks, status_filter=status_filter)
    except Exception as e:
        current_app.logger.exception(f"Error loading tasks: {e}")
        return render_template("communication/staff_tasks.html", tasks=[], status_filter=None)

@comm_bp.route("/tasks/new", methods=["GET", "POST"])
@login_required
@role_required(UserRole.Admin, UserRole.SalesManager)
def task_new():
    """Create a new task."""
    if request.method == "POST":
        try:
            assigned_to = request.form.get('assigned_to', type=int)
            if not assigned_to:
                flash("Please select a user to assign the task to.", "danger")
                return redirect(url_for("communication.task_new"))
            
            data = {
                'title': request.form.get('title', '').strip(),
                'details': request.form.get('details', '').strip(),
                'priority': request.form.get('priority', 'medium'),
                'due_date': request.form.get('due_date', ''),
                'status': 'pending'
            }
            
            if not data['title']:
                flash("Task title is required.", "danger")
                return redirect(url_for("communication.task_new"))
            
            result = create_task(assigned_to, current_user.id, data)
            
            if result['success']:
                flash("Task created successfully!", "success")
                return redirect(url_for("communication.staff_tasks"))
            else:
                flash(f"Error: {result.get('error', 'Unknown error')}", "danger")
        except Exception as e:
            current_app.logger.exception(f"Error creating task: {e}")
    
    # Get all users for assignment
    users = User.query.order_by(User.email.asc()).all()
    return render_template("communication/task_form.html", users=users)

@comm_bp.route("/tasks/<int:task_id>/update", methods=["POST"])
@login_required
def task_update(task_id):
    """Update task status."""
    try:
        task = StaffTask.query.get_or_404(task_id)
        
        # Verify user can update this task
        if task.assigned_to != current_user.id and current_user.role != UserRole.Admin:
            flash("You do not have permission to update this task.", "danger")
            return redirect(url_for("communication.staff_tasks"))
        
        status = request.form.get('status', task.status)
        result = update_task_status(task_id, status, current_user.id)
        
        if result['success']:
            flash("Task updated!", "success")
        else:
            flash(f"Error: {result.get('error', 'Unknown error')}", "danger")
    except Exception as e:
        current_app.logger.exception(f"Error updating task: {e}")
    
    return redirect(url_for("communication.staff_tasks"))

# ============================
# FILE SERVING
# ============================

@comm_bp.route("/uploads/<path:filename>")
@login_required
def serve_upload(filename):
    """Serve uploaded files."""
    try:
        upload_folder = get_upload_folder()
        return send_from_directory(upload_folder, filename)
    except Exception as e:
        current_app.logger.exception(f"Error serving file: {e}")
        flash("File not found.", "danger")
        return redirect(url_for("communication.dashboard"))

