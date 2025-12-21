"""Communication Hub Service - Business logic for announcements, messages, tasks."""
import os
from datetime import datetime, date
from flask import current_app
from werkzeug.utils import secure_filename
from sas_management.models import (
    db, Announcement, BulletinPost, DirectMessageThread, DirectMessage,
    DepartmentMessage, EventMessageThread, EventMessage, StaffTask,
    User, Event
)


ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'pdf', 'doc', 'docx', 'txt'}


def allowed_file(filename):
    """Check if file extension is allowed."""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def get_upload_folder():
    """Get the upload folder for communication files."""
    upload_folder = os.path.join(current_app.instance_path, 'comm_uploads', 'attachments')
    os.makedirs(upload_folder, exist_ok=True)
    return upload_folder


# ============================
# ANNOUNCEMENTS
# ============================

def create_announcement(data, image_file=None):
    """Create a new announcement."""
    try:
        announcement = Announcement(
            title=data.get('title', '').strip(),
            message=data.get('message', '').strip(),
            created_by=data.get('created_by')
        )
        
        # Handle image upload
        if image_file and image_file.filename and allowed_file(image_file.filename):
            filename = secure_filename(f"announcement_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}_{image_file.filename}")
            upload_folder = get_upload_folder()
            image_path = os.path.join(upload_folder, filename)
            image_file.save(image_path)
            announcement.image_url = f"comm_uploads/attachments/{filename}"
        
        db.session.add(announcement)
        db.session.commit()
        
        return {"success": True, "announcement": announcement}
    except Exception as e:
        db.session.rollback()
        current_app.logger.exception(f"Error creating announcement: {e}")
        return {"success": False, "error": str(e)}


def list_announcements(limit=None):
    """Get all announcements, most recent first."""
    try:
        query = Announcement.query.order_by(Announcement.created_at.desc())
        if limit:
            announcements = query.limit(limit).all()
        else:
            announcements = query.all()
        return {"success": True, "announcements": announcements}
    except Exception as e:
        current_app.logger.exception(f"Error listing announcements: {e}")
        return {"success": False, "error": str(e), "announcements": []}


def get_announcement(announcement_id):
    """Get a specific announcement."""
    try:
        announcement = db.session.get(Announcement, announcement_id)
        if not announcement:
            return {"success": False, "error": "Announcement not found"}
        return {"success": True, "announcement": announcement}
    except Exception as e:
        current_app.logger.exception(f"Error getting announcement: {e}")
        return {"success": False, "error": str(e)}


# ============================
# BULLETIN
# ============================

def add_bulletin_post(message, user_id):
    """Add a bulletin board post."""
    try:
        post = BulletinPost(
            message=message.strip(),
            created_by=user_id
        )
        db.session.add(post)
        db.session.commit()
        return {"success": True, "post": post}
    except Exception as e:
        db.session.rollback()
        current_app.logger.exception(f"Error adding bulletin post: {e}")
        return {"success": False, "error": str(e)}


def get_bulletin(limit=50):
    """Get bulletin posts, most recent first."""
    try:
        posts = BulletinPost.query.order_by(BulletinPost.created_at.desc()).limit(limit).all()
        return {"success": True, "posts": posts}
    except Exception as e:
        current_app.logger.exception(f"Error getting bulletin: {e}")
        return {"success": False, "error": str(e), "posts": []}


# ============================
# DIRECT MESSAGING
# ============================

def get_or_create_thread(user_a, user_b):
    """Get or create a direct message thread between two users."""
    try:
        # Ensure consistent ordering (smaller ID first)
        if user_a > user_b:
            user_a, user_b = user_b, user_a
        
        thread = DirectMessageThread.query.filter_by(
            user_a=user_a,
            user_b=user_b
        ).first()
        
        if not thread:
            thread = DirectMessageThread(
                user_a=user_a,
                user_b=user_b
            )
            db.session.add(thread)
            db.session.commit()
            db.session.refresh(thread)
        
        return {"success": True, "thread": thread}
    except Exception as e:
        db.session.rollback()
        current_app.logger.exception(f"Error getting/creating thread: {e}")
        return {"success": False, "error": str(e)}


def send_direct_message(thread_id, sender_id, text, attachment_file=None):
    """Send a direct message in a thread."""
    try:
        message = DirectMessage(
            thread_id=thread_id,
            sender_id=sender_id,
            message=text.strip()
        )
        
        # Handle attachment
        if attachment_file and attachment_file.filename and allowed_file(attachment_file.filename):
            filename = secure_filename(f"dm_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}_{attachment_file.filename}")
            upload_folder = get_upload_folder()
            file_path = os.path.join(upload_folder, filename)
            attachment_file.save(file_path)
            message.attachment = f"comm_uploads/attachments/{filename}"
        
        db.session.add(message)
        db.session.commit()
        
        return {"success": True, "message": message}
    except Exception as e:
        db.session.rollback()
        current_app.logger.exception(f"Error sending direct message: {e}")
        return {"success": False, "error": str(e)}


def get_thread_messages(thread_id):
    """Get all messages in a thread."""
    try:
        messages = DirectMessage.query.filter_by(thread_id=thread_id).order_by(DirectMessage.timestamp.asc()).all()
        return {"success": True, "messages": messages}
    except Exception as e:
        current_app.logger.exception(f"Error getting thread messages: {e}")
        return {"success": False, "error": str(e), "messages": []}


def get_user_threads(user_id):
    """Get all threads for a user."""
    try:
        threads = DirectMessageThread.query.filter(
            (DirectMessageThread.user_a == user_id) | (DirectMessageThread.user_b == user_id)
        ).order_by(DirectMessageThread.created_at.desc()).all()
        return {"success": True, "threads": threads}
    except Exception as e:
        current_app.logger.exception(f"Error getting user threads: {e}")
        return {"success": False, "error": str(e), "threads": []}


# ============================
# DEPARTMENT MESSAGING
# ============================

def post_department_message(department, message, sender_id, attachment_file=None):
    """Post a message to a department."""
    try:
        dept_message = DepartmentMessage(
            department=department.strip(),
            message=message.strip(),
            sender_id=sender_id
        )
        
        # Handle attachment
        if attachment_file and attachment_file.filename and allowed_file(attachment_file.filename):
            filename = secure_filename(f"dept_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}_{attachment_file.filename}")
            upload_folder = get_upload_folder()
            file_path = os.path.join(upload_folder, filename)
            attachment_file.save(file_path)
            dept_message.attachment = f"comm_uploads/attachments/{filename}"
        
        db.session.add(dept_message)
        db.session.commit()
        
        return {"success": True, "message": dept_message}
    except Exception as e:
        db.session.rollback()
        current_app.logger.exception(f"Error posting department message: {e}")
        return {"success": False, "error": str(e)}


def get_department_messages(department, limit=100):
    """Get messages for a department."""
    try:
        messages = DepartmentMessage.query.filter_by(
            department=department
        ).order_by(DepartmentMessage.created_at.desc()).limit(limit).all()
        return {"success": True, "messages": messages}
    except Exception as e:
        current_app.logger.exception(f"Error getting department messages: {e}")
        return {"success": False, "error": str(e), "messages": []}


# ============================
# EVENT MESSAGING
# ============================

def get_or_create_event_thread(event_id):
    """Get or create a message thread for an event."""
    try:
        thread = EventMessageThread.query.filter_by(event_id=event_id).first()
        
        if not thread:
            thread = EventMessageThread(event_id=event_id)
            db.session.add(thread)
            db.session.commit()
            db.session.refresh(thread)
        
        return {"success": True, "thread": thread}
    except Exception as e:
        db.session.rollback()
        current_app.logger.exception(f"Error getting/creating event thread: {e}")
        return {"success": False, "error": str(e)}


def post_event_message(thread_id, sender_id, text, attachment_file=None):
    """Post a message in an event thread."""
    try:
        message = EventMessage(
            thread_id=thread_id,
            sender_id=sender_id,
            message=text.strip()
        )
        
        # Handle attachment
        if attachment_file and attachment_file.filename and allowed_file(attachment_file.filename):
            filename = secure_filename(f"event_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}_{attachment_file.filename}")
            upload_folder = get_upload_folder()
            file_path = os.path.join(upload_folder, filename)
            attachment_file.save(file_path)
            message.attachment = f"comm_uploads/attachments/{filename}"
        
        db.session.add(message)
        db.session.commit()
        
        return {"success": True, "message": message}
    except Exception as e:
        db.session.rollback()
        current_app.logger.exception(f"Error posting event message: {e}")
        return {"success": False, "error": str(e)}


def get_event_thread_messages(thread_id):
    """Get all messages in an event thread."""
    try:
        messages = EventMessage.query.filter_by(thread_id=thread_id).order_by(EventMessage.timestamp.asc()).all()
        return {"success": True, "messages": messages}
    except Exception as e:
        current_app.logger.exception(f"Error getting event thread messages: {e}")
        return {"success": False, "error": str(e), "messages": []}


# ============================
# STAFF TASKS
# ============================

def create_task(assigned_to, assigned_by, data):
    """Create a new staff task."""
    try:
        due_date_str = data.get('due_date')
        due_date = None
        if due_date_str:
            try:
                due_date = datetime.strptime(due_date_str, '%Y-%m-%d').date()
            except ValueError:
                pass
        
        task = StaffTask(
            assigned_to=assigned_to,
            assigned_by=assigned_by,
            title=data.get('title', '').strip(),
            details=data.get('details', '').strip() or None,
            priority=data.get('priority', 'medium').lower(),
            due_date=due_date,
            status=data.get('status', 'pending')
        )
        
        db.session.add(task)
        db.session.commit()
        
        return {"success": True, "task": task}
    except Exception as e:
        db.session.rollback()
        current_app.logger.exception(f"Error creating task: {e}")
        return {"success": False, "error": str(e)}


def update_task_status(task_id, status, user_id=None):
    """Update task status."""
    try:
        task = db.session.get(StaffTask, task_id)
        if not task:
            return {"success": False, "error": "Task not found"}
        
        task.status = status
        if status == 'completed':
            task.completed_at = datetime.utcnow()
        
        db.session.commit()
        
        return {"success": True, "task": task}
    except Exception as e:
        db.session.rollback()
        current_app.logger.exception(f"Error updating task status: {e}")
        return {"success": False, "error": str(e)}


def list_tasks_for_user(user_id, status_filter=None):
    """Get tasks for a user."""
    try:
        query = StaffTask.query.filter_by(assigned_to=user_id)
        if status_filter:
            query = query.filter_by(status=status_filter)
        tasks = query.order_by(StaffTask.created_at.desc()).all()
        return {"success": True, "tasks": tasks}
    except Exception as e:
        current_app.logger.exception(f"Error listing tasks: {e}")
        return {"success": False, "error": str(e), "tasks": []}


def get_task(task_id):
    """Get a specific task."""
    try:
        task = db.session.get(StaffTask, task_id)
        if not task:
            return {"success": False, "error": "Task not found"}
        return {"success": True, "task": task}
    except Exception as e:
        current_app.logger.exception(f"Error getting task: {e}")
        return {"success": False, "error": str(e)}

