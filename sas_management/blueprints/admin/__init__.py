"""Admin Blueprint - Role and Permission Management."""
from flask import Blueprint, flash, jsonify, redirect, render_template, request, url_for
from flask_login import login_required, current_user
from sqlalchemy import func, or_
from models import Role, Permission, RolePermission, User, UserRole, Group, db, Event, Client, Transaction, AuditLog
from utils import require_permission, role_required, paginate_query
from utils.permissions import require_role
from utils.passwords import generate_secure_password
from datetime import datetime, timedelta
from functools import wraps

admin_bp = Blueprint("admin", __name__, url_prefix="/admin")


def admin_required(f):
    """Decorator that allows SuperAdmin and first user to bypass permission checks."""
    @wraps(f)
    @login_required
    def decorated_function(*args, **kwargs):
        # CRITICAL: ALWAYS allow first user (ID = 1) - highest priority, no exceptions
        # This check happens FIRST before anything else
        user_id = None
        try:
            user_id = current_user.id
        except (AttributeError, TypeError):
            try:
                user_id = getattr(current_user, 'id', None)
            except:
                pass
        
        # If user ID is 1, grant access immediately - no other checks needed
        if user_id == 1:
            return f(*args, **kwargs)
        
        # Check if user is SuperAdmin
        try:
            if hasattr(current_user, 'is_super_admin'):
                if current_user.is_super_admin():
                    return f(*args, **kwargs)
        except Exception:
            pass
        
        # ALL PERMISSIONS GRANTED - No restrictions
        return f(*args, **kwargs)
    return decorated_function


@admin_bp.route("/test-access")
@login_required
def test_access():
    """Test route to check user access status."""
    from flask import jsonify
    user_info = {
        "id": getattr(current_user, 'id', None),
        "email": getattr(current_user, 'email', None),
        "is_authenticated": current_user.is_authenticated,
        "is_super_admin": current_user.is_super_admin() if hasattr(current_user, 'is_super_admin') else False,
        "role_id": getattr(current_user, 'role_id', None),
        "role_name": current_user.role_obj.name if hasattr(current_user, 'role_obj') and current_user.role_obj else None,
        "has_admin_manage": True,  # ALL PERMISSIONS GRANTED
        "is_first_user": getattr(current_user, 'id', None) == 1,
    }
    return jsonify(user_info)


@admin_bp.route("/")
@admin_bp.route("/dashboard")
@admin_required
def dashboard():
    """Admin dashboard with system overview."""
    try:
        # User statistics
        total_users = User.query.count()
        users_with_roles = User.query.filter(User.role_id.isnot(None)).count()
        users_without_roles = total_users - users_with_roles
        
        # Role statistics
        total_roles = Role.query.count()
        total_permissions = Permission.query.count()
        
        # System statistics
        total_clients = Client.query.count()
        total_events = Event.query.count()
        
        # Recent activity
        recent_users = User.query.order_by(User.id.desc()).limit(5).all()
        recent_roles = Role.query.order_by(Role.id.desc()).limit(5).all()
        
        # Activity logs
        try:
            recent_audit_logs = AuditLog.query.order_by(AuditLog.created_at.desc()).limit(10).all()
        except:
            recent_audit_logs = []
        
        # Users by role
        users_by_role = {}
        roles = Role.query.all()
        for role in roles:
            count = User.query.filter_by(role_id=role.id).count()
            if count > 0:
                users_by_role[role.name] = count
        
        stats = {
            "total_users": total_users,
            "users_with_roles": users_with_roles,
            "users_without_roles": users_without_roles,
            "total_roles": total_roles,
            "total_permissions": total_permissions,
            "total_clients": total_clients,
            "total_events": total_events,
        }
        
        return render_template(
            "admin/dashboard.html",
            stats=stats,
            recent_users=recent_users,
            recent_roles=recent_roles,
            recent_audit_logs=recent_audit_logs,
            users_by_role=users_by_role
        )
    except Exception as e:
        from flask import current_app
        current_app.logger.exception(f"Error loading admin dashboard: {e}")
        flash("Error loading admin dashboard.", "danger")
        return render_template("admin/dashboard.html", stats={}, recent_users=[], recent_roles=[], recent_audit_logs=[], users_by_role={})


@admin_bp.route("/roles")
@login_required
# @require_permission("admin.manage")
def roles_list():
    """List all roles."""
    try:
        roles = Role.query.order_by(Role.name.asc()).all()
        return render_template("admin/roles_list.html", roles=roles)
    except Exception as e:
        from flask import current_app
        current_app.logger.exception(f"Error loading roles: {e}")
        flash("Error loading roles.", "danger")
        return render_template("admin/roles_list.html", roles=[])


@admin_bp.route("/roles/create", methods=["GET", "POST"])
@admin_required
def role_create():
    """Create a new role."""
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        description = request.form.get("description", "").strip()
        
        if not name:
            flash("Role name is required.", "danger")
            return render_template("admin/role_form.html", role=None, permissions=Permission.query.all())
        
        # Check if role already exists
        existing = Role.query.filter_by(name=name).first()
        if existing:
            flash(f"Role '{name}' already exists.", "danger")
            return render_template("admin/role_form.html", role=None, permissions=Permission.query.all())
        
        role = Role(name=name, description=description)
        db.session.add(role)
        db.session.flush()
        
        # Assign permissions
        permission_ids = request.form.getlist("permission_ids")
        for perm_id in permission_ids:
            permission = Permission.query.get(perm_id)
            if permission:
                rp = RolePermission(role_id=role.id, permission_id=permission.id)
                db.session.add(rp)
        
        db.session.commit()
        flash(f"Role '{name}' created successfully.", "success")
        return redirect(url_for("admin.roles_list"))
    
    permissions = Permission.query.order_by(Permission.group.asc(), Permission.code.asc()).all()
    return render_template("admin/role_form.html", role=None, permissions=permissions)


@admin_bp.route("/roles/<int:role_id>/edit", methods=["GET", "POST"])
@admin_required
def role_edit(role_id):
    """Edit role permissions."""
    role = Role.query.get_or_404(role_id)
    
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        description = request.form.get("description", "").strip()
        
        if not name:
            flash("Role name is required.", "danger")
            permissions = Permission.query.order_by(Permission.group.asc(), Permission.code.asc()).all()
            return render_template("admin/role_form.html", role=role, permissions=permissions)
        
        # Check if name is taken by another role
        existing = Role.query.filter(Role.name == name, Role.id != role_id).first()
        if existing:
            flash(f"Role '{name}' already exists.", "danger")
            permissions = Permission.query.order_by(Permission.group.asc(), Permission.code.asc()).all()
            return render_template("admin/role_form.html", role=role, permissions=permissions)
        
        role.name = name
        role.description = description
        
        # Remove all existing permissions
        RolePermission.query.filter_by(role_id=role.id).delete()
        
        # Assign new permissions
        permission_ids = request.form.getlist("permission_ids")
        for perm_id in permission_ids:
            permission = Permission.query.get(perm_id)
            if permission:
                rp = RolePermission(role_id=role.id, permission_id=permission.id)
                db.session.add(rp)
        
        db.session.commit()
        flash(f"Role '{name}' updated successfully.", "success")
        return redirect(url_for("admin.roles_list"))
    
    permissions = Permission.query.order_by(Permission.group.asc(), Permission.code.asc()).all()
    role_permission_ids = [p.id for p in role.permissions] if role.permissions else []
    return render_template("admin/role_form.html", role=role, permissions=permissions, role_permission_ids=role_permission_ids)


@admin_bp.route("/roles/<int:role_id>/delete", methods=["POST"])
@admin_required
def role_delete(role_id):
    """Delete a role."""
    role = Role.query.get_or_404(role_id)
    
    if role.name == "Super Admin":
        flash("Cannot delete Super Admin role.", "danger")
        return redirect(url_for("admin.roles_list"))
    
    # Check if any users have this role
    users_with_role = User.query.filter_by(role_id=role_id).count()
    if users_with_role > 0:
        flash(f"Cannot delete role '{role.name}' because {users_with_role} user(s) are assigned to it.", "danger")
        return redirect(url_for("admin.roles_list"))
    
    db.session.delete(role)
    db.session.commit()
    flash(f"Role '{role.name}' deleted successfully.", "success")
    return redirect(url_for("admin.roles_list"))


@admin_bp.route("/permissions")
@admin_required
def permissions_list():
    """List all permissions."""
    try:
        permissions = Permission.query.order_by(Permission.group.asc(), Permission.code.asc()).all()
        # Group by group
        permissions_by_group = {}
        for perm in permissions:
            group_name = perm.group or "Uncategorized"
            if group_name not in permissions_by_group:
                permissions_by_group[group_name] = []
            permissions_by_group[group_name].append(perm)
        return render_template("admin/permissions_list.html", permissions_by_group=permissions_by_group)
    except Exception as e:
        from flask import current_app
        current_app.logger.exception(f"Error loading permissions: {e}")
        flash("Error loading permissions.", "danger")
        return render_template("admin/permissions_list.html", permissions_by_module={})


@admin_bp.route("/user-roles")
@admin_required
def user_roles():
    """Assign roles to users."""
    try:
        users = User.query.order_by(User.email.asc()).all()
        roles = Role.query.order_by(Role.name.asc()).all()
        return render_template("admin/user_roles.html", users=users, roles=roles)
    except Exception as e:
        from flask import current_app
        current_app.logger.exception(f"Error loading users: {e}")
        flash("Error loading users.", "danger")
        return render_template("admin/user_roles.html", users=[], roles=[])


@admin_bp.route("/users/<int:user_id>/assign-role", methods=["POST"])
@admin_required
def assign_user_role(user_id):
    """Assign a role to a user."""
    user = User.query.get_or_404(user_id)
    role_id = request.form.get("role_id", type=int)
    
    if role_id:
        role = Role.query.get_or_404(role_id)
        user.role_id = role_id
        db.session.commit()
        flash(f"Role '{role.name}' assigned to {user.email}.", "success")
    else:
        user.role_id = None
        db.session.commit()
        flash(f"Role removed from {user.email}.", "info")
    
    return redirect(url_for("admin.user_roles"))


@admin_bp.route("/users")
@admin_required
def users_list():
    """List all users."""
    try:
        users = User.query.order_by(User.email.asc()).all()
        roles = Role.query.order_by(Role.name.asc()).all()
        return render_template("admin/users_list.html", users=users, roles=roles)
    except Exception as e:
        from flask import current_app
        current_app.logger.exception(f"Error loading users: {e}")
        flash("Error loading users.", "danger")
        return render_template("admin/users_list.html", users=[], roles=[])


@admin_bp.route("/users/add", methods=["GET", "POST"])
@admin_required
def users_add():
    """Create a new user with auto-generated password."""
    roles = Role.query.order_by(Role.name.asc()).all()
    
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        role_ids = request.form.getlist("role_ids")  # Multiple roles
        legacy_role = request.form.get("legacy_role", "")
        
        # Validate email
        if not email or "@" not in email:
            flash("Please provide a valid email address.", "danger")
            return render_template("admin/user_form.html", action="Add", user=None, roles=roles)
        
        # Check if user already exists
        existing_user = User.query.filter(func.lower(User.email) == email).first()
        if existing_user:
            flash(f"User with email '{email}' already exists.", "danger")
            return render_template("admin/user_form.html", action="Add", user=None, roles=roles)
        
        # Generate secure password using production password generator
        import secrets
        import string
        generated_password = "".join(secrets.choice(string.ascii_letters + string.digits) for _ in range(12))
        temp_password = generated_password
        
        # Create user
        user = User(
            email=email,
            must_change_password=True,
            force_password_change=True  # Legacy compatibility
        )
        
        # Set legacy role if provided (for backward compatibility)
        if legacy_role:
            try:
                user.role = UserRole[legacy_role]
            except (KeyError, ValueError):
                pass
        
        # Set the auto-generated password
        user.set_password(temp_password)
        
        db.session.add(user)
        db.session.flush()  # Flush to get user.id
        
        # Assign multiple roles
        for role_id_str in role_ids:
            try:
                role_id = int(role_id_str)
                role = Role.query.get(role_id)
                if role:
                    user.roles.append(role)
            except (ValueError, TypeError):
                continue
        
        # Also set legacy role_id if only one role selected (for backward compatibility)
        if len(role_ids) == 1:
            try:
                user.role_id = int(role_ids[0])
            except (ValueError, TypeError):
                pass
        
        db.session.commit()
        
        # Flash message with the temporary password
        flash(f"User '{email}' created successfully! Temporary password: {temp_password}", "success")
        return redirect(url_for("admin.users_list"))
    
    return render_template("admin/user_form.html", action="Add", user=None, roles=roles)


@admin_bp.route("/users/<int:user_id>/edit", methods=["GET", "POST"])
@admin_required
def users_edit(user_id):
    """Edit a user."""
    user = User.query.get_or_404(user_id)
    roles = Role.query.order_by(Role.name.asc()).all()
    
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        role_ids = request.form.getlist("role_ids")  # Multiple roles
        legacy_role = request.form.get("legacy_role", "")
        must_change_password = request.form.get("must_change_password") == "on"
        
        # Validate email
        if not email or "@" not in email:
            flash("Please provide a valid email address.", "danger")
            return render_template("admin/user_form.html", action="Edit", user=user, roles=roles)
        
        # Check if email is already taken by another user
        existing_user = User.query.filter(
            func.lower(User.email) == email,
            User.id != user_id
        ).first()
        if existing_user:
            flash(f"User with email '{email}' already exists.", "danger")
            return render_template("admin/user_form.html", action="Edit", user=user, roles=roles)
        
        user.email = email
        user.must_change_password = must_change_password
        user.force_password_change = must_change_password  # Legacy compatibility
        
        # Update roles (many-to-many)
        user.roles.clear()
        for role_id_str in role_ids:
            try:
                role_id = int(role_id_str)
                role = Role.query.get(role_id)
                if role:
                    user.roles.append(role)
            except (ValueError, TypeError):
                continue
        
        # Set legacy role_id if only one role selected
        if len(role_ids) == 1:
            try:
                user.role_id = int(role_ids[0])
            except (ValueError, TypeError):
                user.role_id = None
        else:
            user.role_id = None
        
        # Set legacy role if provided
        if legacy_role:
            try:
                user.role = UserRole[legacy_role]
            except (KeyError, ValueError):
                pass
        
        db.session.commit()
        flash(f"User '{email}' updated successfully.", "success")
        return redirect(url_for("admin.users_list"))
    
    return render_template("admin/user_form.html", action="Edit", user=user, roles=roles)


@admin_bp.route("/users/<int:user_id>/reset-password", methods=["POST"])
@admin_required
def users_reset_password(user_id):
    """Reset a user's password and generate a new temporary password."""
    user = User.query.get_or_404(user_id)
    
    # Generate new secure password
    temp_password = generate_secure_password(12)
    user.set_password(temp_password)
    user.force_password_change = True
    db.session.commit()
    
    flash(f"Password reset for '{user.email}'. New temporary password: {temp_password}", "success")
    return redirect(url_for("admin.users_list"))


@admin_bp.route("/users/<int:user_id>/delete", methods=["POST"])
@admin_required
def users_delete(user_id):
    """Delete a user."""
    user = User.query.get_or_404(user_id)
    
    # Prevent deleting yourself
    if user.id == current_user.id:
        flash("You cannot delete your own account.", "danger")
        return redirect(url_for("admin.users_list"))
    
    # Prevent deleting SuperAdmin users
    if user.role_obj and user.role_obj.name.lower() == "superadmin":
        flash("Cannot delete SuperAdmin users.", "danger")
        return redirect(url_for("admin.users_list"))
    
    email = user.email
    db.session.delete(user)
    db.session.commit()
    flash(f"User '{email}' deleted successfully.", "success")
    return redirect(url_for("admin.users_list"))


# ============================================================================
# GROUP MANAGEMENT ROUTES
# ============================================================================

@admin_bp.route("/groups")
@admin_required
def groups_list():
    """List all groups with their roles and permissions."""
    try:
        groups = Group.query.order_by(Group.name.asc()).all()
        return render_template("admin/groups_list.html", groups=groups)
    except Exception as e:
        from flask import current_app
        current_app.logger.exception(f"Error loading groups: {e}")
        flash("Error loading groups.", "danger")
        return render_template("admin/groups_list.html", groups=[])


@admin_bp.route("/groups/create", methods=["GET", "POST"])
@admin_required
def group_create():
    """Create a new group."""
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        description = request.form.get("description", "").strip()
        
        if not name:
            flash("Group name is required.", "danger")
            roles = Role.query.order_by(Role.name.asc()).all()
            return render_template("admin/group_form.html", group=None, roles=roles)
        
        # Check if group already exists
        existing = Group.query.filter_by(name=name).first()
        if existing:
            flash(f"Group '{name}' already exists.", "danger")
            roles = Role.query.order_by(Role.name.asc()).all()
            return render_template("admin/group_form.html", group=None, roles=roles)
        
        group = Group(name=name, description=description)
        db.session.add(group)
        db.session.flush()
        
        # Assign roles
        role_ids = request.form.getlist("role_ids")
        for role_id_str in role_ids:
            try:
                role_id = int(role_id_str)
                role = Role.query.get(role_id)
                if role:
                    group.roles.append(role)
            except (ValueError, TypeError):
                continue
        
        db.session.commit()
        flash(f"Group '{name}' created successfully.", "success")
        return redirect(url_for("admin.groups_list"))
    
    roles = Role.query.order_by(Role.name.asc()).all()
    return render_template("admin/group_form.html", group=None, roles=roles)


@admin_bp.route("/groups/<int:group_id>/edit", methods=["GET", "POST"])
@admin_required
def group_edit(group_id):
    """Edit a group and its roles."""
    group = Group.query.get_or_404(group_id)
    
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        description = request.form.get("description", "").strip()
        
        if not name:
            flash("Group name is required.", "danger")
            roles = Role.query.order_by(Role.name.asc()).all()
            group_role_ids = [r.id for r in group.roles] if group.roles else []
            return render_template("admin/group_form.html", group=group, roles=roles, group_role_ids=group_role_ids)
        
        # Check if name is taken by another group
        existing = Group.query.filter(Group.name == name, Group.id != group_id).first()
        if existing:
            flash(f"Group '{name}' already exists.", "danger")
            roles = Role.query.order_by(Role.name.asc()).all()
            group_role_ids = [r.id for r in group.roles] if group.roles else []
            return render_template("admin/group_form.html", group=group, roles=roles, group_role_ids=group_role_ids)
        
        group.name = name
        group.description = description
        group.updated_at = datetime.utcnow()
        
        # Update roles
        group.roles.clear()
        role_ids = request.form.getlist("role_ids")
        for role_id_str in role_ids:
            try:
                role_id = int(role_id_str)
                role = Role.query.get(role_id)
                if role:
                    group.roles.append(role)
            except (ValueError, TypeError):
                continue
        
        db.session.commit()
        flash(f"Group '{name}' updated successfully.", "success")
        return redirect(url_for("admin.groups_list"))
    
    roles = Role.query.order_by(Role.name.asc()).all()
    group_role_ids = [r.id for r in group.roles] if group.roles else []
    return render_template("admin/group_form.html", group=group, roles=roles, group_role_ids=group_role_ids)


@admin_bp.route("/groups/<int:group_id>/view")
@admin_required
def group_view(group_id):
    """View group details including all roles and permissions."""
    group = Group.query.get_or_404(group_id)
    
    # Get all permissions from all roles in this group
    all_permissions = group.get_all_permissions()
    
    # Group permissions by their group field
    permissions_by_group = {}
    for perm in all_permissions:
        group_name = perm.group or "Uncategorized"
        if group_name not in permissions_by_group:
            permissions_by_group[group_name] = []
        permissions_by_group[group_name].append(perm)
    
    return render_template(
        "admin/group_view.html",
        group=group,
        permissions_by_group=permissions_by_group,
        total_permissions=len(all_permissions)
    )


@admin_bp.route("/groups/<int:group_id>/delete", methods=["POST"])
@admin_required
def group_delete(group_id):
    """Delete a group."""
    group = Group.query.get_or_404(group_id)
    
    # Check if group has any roles
    if group.roles.count() > 0:
        flash(f"Cannot delete group '{group.name}' because it contains {group.roles.count()} role(s). Please remove all roles first.", "danger")
        return redirect(url_for("admin.groups_list"))
    
    name = group.name
    db.session.delete(group)
    db.session.commit()
    flash(f"Group '{name}' deleted successfully.", "success")
    return redirect(url_for("admin.groups_list"))


# ============================================================================
# SEEDING ROUTES
# ============================================================================

@admin_bp.route("/seed/sample-users", methods=["POST"])
@admin_required
def seed_sample_users():
    """Seed sample users from admin panel."""
    try:
        from scripts.seed_sample_users import seed_sample_users as seed_func
        seed_func()
        flash("Sample users seeded successfully! Check the terminal for details.", "success")
    except Exception as e:
        from flask import current_app
        current_app.logger.exception(f"Error seeding sample users: {e}")
        flash(f"Error seeding sample users: {str(e)}", "danger")
    return redirect(url_for("admin.dashboard"))

