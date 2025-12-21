from datetime import date, datetime

from flask import Blueprint, current_app, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required
from sqlalchemy.orm import joinedload

from sas_management.models import Event, Task, TaskStatus, User, UserRole, db
from sas_management.utils import role_required, paginate_query

tasks_bp = Blueprint("tasks", __name__, url_prefix="/tasks")

@tasks_bp.route("")
@login_required
def task_list():
    """Task dashboard - users see tasks assigned to them, admins see all tasks."""
    if current_user.is_super_admin() or current_user.role == UserRole.Admin:
        query = Task.query.order_by(Task.due_date.asc(), Task.status.asc())
    else:
        query = Task.query.filter(Task.assigned_user_id == current_user.id).order_by(
            Task.due_date.asc(), Task.status.asc()
        )

    pagination = paginate_query(
        query.options(joinedload(Task.assigned_user), joinedload(Task.event))
    )
    return render_template("tasks/list.html", tasks=pagination.items, pagination=pagination)

@tasks_bp.route("/add", methods=["GET", "POST"])
@login_required
@role_required(UserRole.Admin, UserRole.SalesManager)
def task_add():
    events = Event.query.order_by(Event.event_date.desc()).all()
    users = User.query.order_by(User.email.asc()).all()

    if request.method == "POST":
        event_id = request.form.get("event_id", type=int) or None
        assigned_user_id = request.form.get("assigned_user_id", type=int) or None
        due_date_str = request.form.get("due_date", "")
        try:
            due_date = datetime.strptime(due_date_str, "%Y-%m-%d").date() if due_date_str else None
        except ValueError:
            due_date = None

        task = Task(
            title=request.form.get("title", "").strip(),
            description=request.form.get("description", "").strip() or None,
            event_id=event_id,
            assigned_user_id=assigned_user_id,
            due_date=due_date,
            status=TaskStatus.Pending,
        )
        db.session.add(task)
        db.session.commit()
        flash("Task created successfully.", "success")
        return redirect(url_for("tasks.task_list"))

    return render_template("tasks/form.html", action="Add", task=None, events=events, users=users)

@tasks_bp.route("/edit/<int:task_id>", methods=["GET", "POST"])
@login_required
def task_edit(task_id):
    task = Task.query.get_or_404(task_id)

    # Users can only edit their own tasks unless they're admin - Admin bypass
    if not (hasattr(current_user, 'is_admin') and current_user.is_admin):
        if current_user.role != UserRole.Admin and task.assigned_user_id != current_user.id:
            flash("You can only edit tasks assigned to you.", "warning")
            return redirect(url_for("tasks.task_list"))

    events = Event.query.order_by(Event.event_date.desc()).all()
    users = User.query.order_by(User.email.asc()).all()

    if request.method == "POST":
        task.title = request.form.get("title", task.title).strip()
        task.description = request.form.get("description", "").strip() or None

        # Admin bypass
        if (hasattr(current_user, 'is_admin') and current_user.is_admin) or current_user.is_super_admin() or current_user.role == UserRole.Admin:
            task.event_id = request.form.get("event_id", type=int) or None
            task.assigned_user_id = request.form.get("assigned_user_id", type=int) or None
            due_date_str = request.form.get("due_date", "")
            try:
                task.due_date = (
                    datetime.strptime(due_date_str, "%Y-%m-%d").date() if due_date_str else None
                )
            except ValueError:
                pass

        # All users can update status
        status_str = request.form.get("status", task.status.value)
        try:
            task.status = TaskStatus(status_str)
        except ValueError:
            pass

        db.session.commit()
        flash("Task updated successfully.", "success")
        return redirect(url_for("tasks.task_list"))

    return render_template("tasks/form.html", action="Edit", task=task, events=events, users=users)

@tasks_bp.route("/delete/<int:task_id>", methods=["POST"])
@login_required
@role_required(UserRole.Admin)
def task_delete(task_id):
    task = Task.query.get_or_404(task_id)
    db.session.delete(task)
    db.session.commit()
    flash("Task deleted.", "info")
    return redirect(url_for("tasks.task_list"))

