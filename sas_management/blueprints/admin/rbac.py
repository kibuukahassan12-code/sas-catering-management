"""
RBAC Management Blueprint - Role and Permission management.
"""
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from models import Role, Permission, RolePermission, User, db
from utils.security import require_permission

rbac_bp = Blueprint("rbac", __name__)


@rbac_bp.route("/roles")
@login_required
# @require_permission("system_admin")
def roles_list():
    """List all roles."""
    roles = Role.query.order_by(Role.name.asc()).all()
    # Create a dict for quick parent lookup in template
    role_dict = {r.id: r for r in roles}
    return render_template("admin/rbac/roles.html", roles=roles, role_dict=role_dict)


@rbac_bp.route("/roles/<int:role_id>/permissions", methods=["GET", "POST"])
@login_required
# @require_permission("system_admin")
def edit_role_permissions(role_id):
    """Assign/unassign permissions to a role."""
    role = Role.query.get_or_404(role_id)
    all_permissions = Permission.query.order_by(Permission.name.asc()).all()
    
    if request.method == "POST":
        # Get selected permission IDs
        selected_permission_ids = request.form.getlist("permission_ids")
        selected_permission_ids = [int(pid) for pid in selected_permission_ids]
        
        # Remove all existing permissions
        RolePermission.query.filter_by(role_id=role.id).delete()
        
        # Add new permissions
        for perm_id in selected_permission_ids:
            rp = RolePermission(role_id=role.id, permission_id=perm_id)
            db.session.add(rp)
        
        db.session.commit()
        flash(f"Permissions updated for role '{role.name}'.", "success")
        return redirect(url_for("rbac.roles_list"))
    
    # Get current permission IDs
    current_permission_ids = [rp.permission_id for rp in role.role_permissions]
    
    return render_template(
        "admin/rbac/edit_role_permissions.html",
        role=role,
        all_permissions=all_permissions,
        current_permission_ids=current_permission_ids
    )


@rbac_bp.route("/permissions")
@login_required
# @require_permission("system_admin")
def permissions_list():
    """View all permissions."""
    permissions = Permission.query.order_by(Permission.name.asc()).all()
    return render_template("admin/rbac/permissions.html", permissions=permissions)


@rbac_bp.route("/users/roles", methods=["GET", "POST"])
@login_required
# @require_permission("assign_roles")
def users_roles():
    """Assign roles to users."""
    users = User.query.order_by(User.email.asc()).all()
    roles = Role.query.order_by(Role.name.asc()).all()
    
    if request.method == "POST":
        user_id = request.form.get("user_id", type=int)
        role_id = request.form.get("role_id", type=int)
        
        user = User.query.get_or_404(user_id)
        if role_id:
            role = Role.query.get_or_404(role_id)
            user.role_id = role.id
            flash(f"Role '{role.name}' assigned to {user.email}.", "success")
        else:
            user.role_id = None
            flash(f"Role removed from {user.email}.", "info")
        
        db.session.commit()
        return redirect(url_for("rbac.users_roles"))
    
    return render_template("admin/rbac/users_roles.html", users=users, roles=roles)


@rbac_bp.route("/logs")
@login_required
# @require_permission("system_admin")
def activity_logs():
    """View activity logs."""
    from models import ActivityLog
    from utils import paginate_query
    
    query = ActivityLog.query.order_by(ActivityLog.timestamp.desc())
    pagination = paginate_query(query)
    
    return render_template("admin/rbac/activity_logs.html", logs=pagination.items, pagination=pagination)

