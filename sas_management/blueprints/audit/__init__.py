
from datetime import timedelta

from flask import Blueprint, current_app, redirect, render_template, request, send_from_directory, url_for
from flask_login import current_user, login_required

from models import AuditLog, User, UserRole, db
from utils import role_required, paginate_query
from utils.helpers import parse_date

audit_bp = Blueprint("audit", __name__, url_prefix="/admin")

@audit_bp.route("/audit_log")
@login_required
@role_required(UserRole.Admin)
def audit_log_list():
    """Admin: View all audit log entries with filtering."""
    # Get filter parameters
    start_date_str = request.args.get("start_date", "")
    end_date_str = request.args.get("end_date", "")
    action_filter = request.args.get("action", "")
    user_id_filter = request.args.get("user_id", type=int)
    resource_type_filter = request.args.get("resource_type", "")
    search_query = request.args.get("search", "").strip()
    
    # Parse dates
    start_date = parse_date(start_date_str) if start_date_str else None
    end_date = parse_date(end_date_str) if end_date_str else None
    
    # Build query with filters
    query = AuditLog.query
    
    # Date range filter
    if start_date:
        query = query.filter(AuditLog.created_at >= start_date)
    if end_date:
        # Add one day to include the entire end date
        query = query.filter(AuditLog.created_at < end_date + timedelta(days=1))
    
    # Action filter
    if action_filter:
        query = query.filter(AuditLog.action == action_filter)
    
    # User filter
    if user_id_filter:
        query = query.filter(AuditLog.user_id == user_id_filter)
    
    # Resource type filter
    if resource_type_filter:
        query = query.filter(AuditLog.resource_type == resource_type_filter)
    
    # Search filter (searches in action, resource_type, details)
    if search_query:
        search_pattern = f"%{search_query}%"
        query = query.filter(
            db.or_(
                AuditLog.action.ilike(search_pattern),
                AuditLog.resource_type.ilike(search_pattern),
                AuditLog.details.ilike(search_pattern)
            )
        )
    
    # Order by created_at descending
    query = query.order_by(AuditLog.created_at.desc())
    
    # Paginate
    pagination = paginate_query(query)
    
    # Get unique values for filter dropdowns
    actions = db.session.query(AuditLog.action).distinct().order_by(AuditLog.action.asc()).all()
    actions = [a[0] for a in actions if a[0]]
    
    resource_types = db.session.query(AuditLog.resource_type).distinct().order_by(AuditLog.resource_type.asc()).all()
    resource_types = [r[0] for r in resource_types if r[0]]
    
    # Get all users who have audit log entries
    users_with_logs = db.session.query(User).join(AuditLog).distinct().order_by(User.email.asc()).all()
    
    return render_template(
        "audit/list.html",
        logs=pagination.items,
        pagination=pagination,
        actions=actions,
        resource_types=resource_types,
        users_with_logs=users_with_logs,
        start_date=start_date_str,
        end_date=end_date_str,
        selected_action=action_filter,
        selected_user_id=user_id_filter,
        selected_resource_type=resource_type_filter,
        search_query=search_query,
    )

