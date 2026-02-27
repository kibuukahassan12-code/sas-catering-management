"""Admin Blueprint - Role and Permission Management."""
from flask import Blueprint, flash, jsonify, redirect, render_template, request, url_for
from flask_login import login_required, current_user
from sqlalchemy import func, or_
from sas_management.models import Role, Permission, RolePermission, User, UserRole, Group, Department, db, Event, Client, Transaction, AuditLog, RoleAssignmentLog, ProductionBudget, ProductionBudgetItem, ProductionBudgetStatus
from sas_management.utils import require_permission, role_required, paginate_query
from sas_management.utils.helpers import get_or_404
from sas_management.utils.permissions import require_role
from sas_management.utils.passwords import generate_secure_password
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

        # Require actual admin privileges for all other users
        try:
            if hasattr(current_user, "is_admin") and current_user.is_admin:
                return f(*args, **kwargs)
        except Exception:
            pass

        return render_template("errors/403.html"), 403
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
        
        # Budget statistics
        try:
            total_budgets = ProductionBudget.query.count()
            draft_budgets = ProductionBudget.query.filter_by(status=ProductionBudgetStatus.Draft).count()
            submitted_budgets = ProductionBudget.query.filter_by(status=ProductionBudgetStatus.Submitted).count()
            approved_budgets = ProductionBudget.query.filter_by(status=ProductionBudgetStatus.Approved).count()
            rejected_budgets = ProductionBudget.query.filter_by(status=ProductionBudgetStatus.Rejected).count()
            pending_review_budgets = ProductionBudget.query.filter_by(status=ProductionBudgetStatus.Submitted).order_by(ProductionBudget.submitted_at.desc()).limit(5).all()
            budget_stats = {
                "total": total_budgets,
                "draft": draft_budgets,
                "submitted": submitted_budgets,
                "approved": approved_budgets,
                "rejected": rejected_budgets,
            }
        except Exception:
            budget_stats = {"total": 0, "draft": 0, "submitted": 0, "approved": 0, "rejected": 0}
            pending_review_budgets = []
        
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
            users_by_role=users_by_role,
            budget_stats=budget_stats,
            pending_review_budgets=pending_review_budgets
        )
    except Exception as e:
        from flask import current_app
        current_app.logger.exception(f"Error loading admin dashboard: {e}")
        flash("Error loading admin dashboard.", "danger")
        return render_template("admin/dashboard.html", stats={}, recent_users=[], recent_roles=[], recent_audit_logs=[], users_by_role={}, budget_stats={"total": 0, "draft": 0, "submitted": 0, "approved": 0, "rejected": 0}, pending_review_budgets=[])


@admin_bp.route("/budgets")
@admin_required
def budgets_list():
    """List all production budgets with admin review functionality."""
    try:
        status_filter = request.args.get("status", "all")
        
        query = ProductionBudget.query
        
        if status_filter == "submitted":
            query = query.filter_by(status=ProductionBudgetStatus.Submitted)
        elif status_filter == "approved":
            query = query.filter_by(status=ProductionBudgetStatus.Approved)
        elif status_filter == "rejected":
            query = query.filter_by(status=ProductionBudgetStatus.Rejected)
        elif status_filter == "draft":
            query = query.filter_by(status=ProductionBudgetStatus.Draft)
        
        budgets = query.order_by(ProductionBudget.created_at.desc()).all()
        
        stats = {
            "total": ProductionBudget.query.count(),
            "draft": ProductionBudget.query.filter_by(status=ProductionBudgetStatus.Draft).count(),
            "submitted": ProductionBudget.query.filter_by(status=ProductionBudgetStatus.Submitted).count(),
            "approved": ProductionBudget.query.filter_by(status=ProductionBudgetStatus.Approved).count(),
            "rejected": ProductionBudget.query.filter_by(status=ProductionBudgetStatus.Rejected).count(),
        }
        
        return render_template("admin/budgets_list.html", budgets=budgets, stats=stats, current_filter=status_filter)
    except Exception as e:
        from flask import current_app
        current_app.logger.exception(f"Error loading budgets: {e}")
        flash("Error loading budgets.", "danger")
        return render_template("admin/budgets_list.html", budgets=[], stats={"total": 0, "draft": 0, "submitted": 0, "approved": 0, "rejected": 0}, current_filter="all")


@admin_bp.route("/budgets/export")
@admin_required
def budgets_export():
    """Export budgets to CSV."""
    try:
        import csv
        from io import StringIO
        from flask import make_response
        
        budgets = ProductionBudget.query.order_by(ProductionBudget.created_at.desc()).all()
        
        # Create CSV
        output = StringIO()
        writer = csv.writer(output)
        
        # Header
        writer.writerow([
            'ID', 'Event', 'Client', 'Status', 'Total Cost (UGX)', 
            'Created', 'Submitted', 'Reviewed By', 'Reviewed At'
        ])
        
        # Data
        for budget in budgets:
            event_title = budget.event.title if budget.event else 'N/A'
            client_name = budget.event.client.name if budget.event and budget.event.client else 'N/A'
            
            writer.writerow([
                budget.id,
                event_title,
                client_name,
                budget.status.value if budget.status else 'N/A',
                budget.total_cost_ugx or 0,
                budget.created_at.strftime('%Y-%m-%d') if budget.created_at else '',
                budget.submitted_at.strftime('%Y-%m-%d') if budget.submitted_at else '',
                budget.reviewed_by or '',
                budget.reviewed_at.strftime('%Y-%m-%d') if budget.reviewed_at else ''
            ])
        
        output.seek(0)
        response = make_response(output.getvalue())
        response.headers['Content-Type'] = 'text/csv'
        response.headers['Content-Disposition'] = f'attachment; filename=budgets_export_{datetime.utcnow().strftime("%Y%m%d")}.csv'
        
        return response
    except Exception as e:
        from flask import current_app
        current_app.logger.exception(f"Error exporting budgets: {e}")
        flash("Error exporting budgets.", "danger")
        return redirect(url_for("admin.budgets_list"))


@admin_bp.route("/budgets/<int:budget_id>/review", methods=["GET", "POST"])
@admin_required
def budget_review(budget_id):
    """Review and approve/reject a production budget."""
    budget = ProductionBudget.query.get_or_404(budget_id)
    
    if request.method == "POST":
        action = request.form.get("action")
        recommendations = request.form.get("admin_recommendations", "").strip()
        
        if action not in ["approve", "reject"]:
            flash("Invalid action.", "danger")
            return redirect(url_for("admin.budget_review", budget_id=budget_id))
        
        if budget.status != ProductionBudgetStatus.Submitted:
            flash("Only submitted budgets can be reviewed.", "warning")
            return redirect(url_for("admin.budgets_list"))
        
        if action == "approve":
            budget.status = ProductionBudgetStatus.Approved
            flash("Budget approved successfully.", "success")
        else:
            budget.status = ProductionBudgetStatus.Rejected
            flash("Budget rejected.", "info")
        
        budget.reviewed_by = current_user.id
        budget.reviewed_at = datetime.utcnow()
        budget.admin_recommendations = recommendations
        db.session.commit()
        
        return redirect(url_for("admin.budgets_list"))
    
    budget_items = ProductionBudgetItem.query.filter_by(budget_id=budget_id).order_by(ProductionBudgetItem.category).all()
    
    return render_template("admin/budget_review.html", budget=budget, budget_items=budget_items)


@admin_bp.route("/roles")
@login_required
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
            permission = db.session.get(Permission, perm_id)
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
    role = get_or_404(Role, role_id)
    
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
            permission = db.session.get(Permission, perm_id)
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
    role = get_or_404(Role, role_id)
    
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
        return render_template("admin/permissions_list.html", permissions_by_group={})


@admin_bp.route("/ai-permissions", methods=["GET", "POST"])
@admin_required
def ai_permissions():
    """
    Manage AI capabilities per role using existing Permission and RolePermission tables.
    """
    from sas_management.ai.permissions import AI_PERMISSIONS

    roles = Role.query.order_by(Role.name.asc()).all()

    # Ensure AI permissions exist and are minimally seeded.
    ai_perms = {}
    try:
        for key, label in AI_PERMISSIONS.items():
            code = f"ai:{key}"
            perm = Permission.query.filter_by(code=code).first()
            if not perm:
                perm = Permission(
                    code=code,
                    name=label,
                    group="AI",
                    module="ai",
                    action="use",
                    description=label,
                )
                db.session.add(perm)
                db.session.flush()

            # Seed: if no role has this permission at all, enable for all roles by default
            existing_count = RolePermission.query.filter_by(
                permission_id=perm.id
            ).count()
            if existing_count == 0:
                for role in roles:
                    db.session.add(
                        RolePermission(role_id=role.id, permission_id=perm.id)
                    )
            ai_perms[key] = perm
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        from flask import current_app

        current_app.logger.warning(f"Error seeding AI permissions: {e}")

    # Reload permissions after potential seeding
    ai_perms = {}
    for key, label in AI_PERMISSIONS.items():
        code = f"ai:{key}"
        perm = Permission.query.filter_by(code=code).first()
        if perm:
            ai_perms[key] = perm

    # Determine selected role
    selected_role_id = request.values.get("role_id", type=int)
    selected_role = None
    if selected_role_id:
        selected_role = Role.query.get(selected_role_id)
    if not selected_role and roles:
        selected_role = roles[0]

    if request.method == "POST" and selected_role:
        # Admin role must always retain full AI access – ignore changes but show as locked.
        is_admin_role = selected_role.name == "Admin"
        if not is_admin_role:
            enabled_codes = set(request.form.getlist("enabled_codes"))
            try:
                for key, perm in ai_perms.items():
                    code = perm.code
                    has_rp = (
                        RolePermission.query.filter_by(
                            role_id=selected_role.id, permission_id=perm.id
                        ).count()
                        > 0
                    )
                    should_enable = code in enabled_codes

                    if should_enable and not has_rp:
                        db.session.add(
                            RolePermission(
                                role_id=selected_role.id, permission_id=perm.id
                            )
                        )
                    elif not should_enable and has_rp:
                        RolePermission.query.filter_by(
                            role_id=selected_role.id, permission_id=perm.id
                        ).delete()

                db.session.commit()
                flash("AI permissions updated successfully.", "success")
            except Exception as e:
                db.session.rollback()
                from flask import current_app

                current_app.logger.error(
                    f"Error updating AI permissions for role {selected_role.id}: {e}"
                )
                flash("Unable to update AI permissions.", "danger")

        # Redirect to avoid form resubmission
        return redirect(
            url_for(
                "admin.ai_permissions",
                role_id=selected_role.id if selected_role else None,
            )
        )

    # Build enabled set for selected role
    enabled_codes = set()
    if selected_role:
        rp_rows = RolePermission.query.filter_by(role_id=selected_role.id).all()
        perm_ids = {rp.permission_id for rp in rp_rows}
        if perm_ids:
            perms = Permission.query.filter(Permission.id.in_(perm_ids)).all()
            enabled_codes = {p.code for p in perms}

    is_admin_role = bool(selected_role and selected_role.name == "Admin")

    return render_template(
        "admin/ai_permissions.html",
        roles=roles,
        selected_role=selected_role,
        ai_permissions=AI_PERMISSIONS,
        ai_perm_rows=ai_perms,
        enabled_codes=enabled_codes,
        is_admin_role=is_admin_role,
    )


@admin_bp.route("/user-roles")
@admin_required
def user_roles():
    """Assign roles to users - Enterprise-grade role assignment."""
    try:
        users = User.query.order_by(User.email.asc()).all()
        roles = Role.query.order_by(Role.name.asc()).all()
        return render_template("admin/user_roles.html", users=users, roles=roles, current_user=current_user, datetime=datetime)
    except Exception as e:
        from flask import current_app
        current_app.logger.exception(f"Error loading users: {e}")
        flash("Error loading users.", "danger")
        return render_template("admin/user_roles.html", users=[], roles=[], current_user=current_user, datetime=datetime)


def log_role_assignment(admin_user_id, affected_user_id, old_role_id, new_role_id, is_bulk=False, is_temporary=False, expiry_date=None, notes=None, ip_address=None):
    """Log role assignment for audit trail."""
    try:
        log_entry = RoleAssignmentLog(
            admin_user_id=admin_user_id,
            affected_user_id=affected_user_id,
            old_role_id=old_role_id,
            new_role_id=new_role_id,
            is_bulk_assignment=is_bulk,
            is_temporary=is_temporary,
            expiry_date=expiry_date,
            notes=notes,
            ip_address=ip_address or request.remote_addr
        )
        db.session.add(log_entry)
        db.session.commit()
    except Exception as e:
        from flask import current_app
        current_app.logger.exception(f"Error logging role assignment: {e}")
        db.session.rollback()


@admin_bp.route("/users/<int:user_id>/assign-role", methods=["GET", "POST"])
@admin_required
def assign_user_role(user_id):
    """
    Assign a role to a user with audit logging.

    GET requests are redirected to the canonical Assign Roles page
    to avoid multiple UI entry points for the same feature.
    """
    if request.method == "GET":
        return redirect(url_for("admin.assign_roles"))
    from sas_management.models import UserRole
    user = get_or_404(User, user_id)
    role_id = request.form.get("role_id", type=int)
    is_temporary = request.form.get("is_temporary") == "true"
    expiry_date_str = request.form.get("expiry_date", "")
    notes = request.form.get("notes", "").strip()
    
    # Parse expiry date if temporary
    expiry_date = None
    if is_temporary and expiry_date_str:
        try:
            expiry_date = datetime.strptime(expiry_date_str, "%Y-%m-%d")
        except ValueError:
            flash("Invalid expiry date format.", "danger")
            return redirect(url_for("admin.user_roles"))
    
    old_role_id = user.role_id
    
    # Admin role protection: Prevent removing or downgrading Admin role
    if user.is_admin:
        if not role_id:
            flash("Cannot remove Admin role from a user. Admin role cannot be downgraded.", "danger")
            return redirect(url_for("admin.user_roles"))
        role = db.session.get(Role, role_id)
        if role and role.name != 'Admin':
            flash("Cannot downgrade Admin role. Admin users must retain Admin role.", "danger")
            return redirect(url_for("admin.user_roles"))
    
    # Prevent removing admin role from current user
    if user.id == current_user.id and user.is_admin:
        if not role_id or (role_id and db.session.get(Role, role_id).name != 'Admin'):
            flash("You cannot remove or downgrade your own Admin role.", "danger")
            return redirect(url_for("admin.user_roles"))
    
    if role_id:
        role = get_or_404(Role, role_id)
        
        # Store previous role if changing
        if old_role_id != role_id:
            user.previous_role_id = old_role_id
        
        user.role_id = role_id
        user.is_temporary_role = is_temporary
        user.role_expiry_date = expiry_date
        user.role_expires_at = expiry_date  # Sync both fields
        
        db.session.commit()
        
        # Log the assignment
        log_role_assignment(
            admin_user_id=current_user.id,
            affected_user_id=user.id,
            old_role_id=old_role_id,
            new_role_id=role_id,
            is_bulk=False,
            is_temporary=is_temporary,
            expiry_date=expiry_date,
            notes=notes
        )
        
        flash(f"Role '{role.name}' assigned to {user.email}.", "success")
    else:
        user.previous_role_id = old_role_id
        user.role_id = None
        user.is_temporary_role = False
        user.role_expiry_date = None
        user.role_expires_at = None  # Sync both fields
        db.session.commit()
        
        # Log the removal
        log_role_assignment(
            admin_user_id=current_user.id,
            affected_user_id=user.id,
            old_role_id=old_role_id,
            new_role_id=None,
            is_bulk=False,
            is_temporary=False,
            notes=notes
        )
        
        flash(f"Role removed from {user.email}.", "info")
    
    return redirect(url_for("admin.user_roles"))


@admin_bp.route("/assign-role", methods=["GET", "POST"])
@admin_required
def assign_role():
    """
    Assign role to one or many users (unified endpoint).

    GET requests are redirected to the canonical Assign Roles page
    to avoid multiple UI entry points for the same feature.
    """
    if request.method == "GET":
        return redirect(url_for("admin.assign_roles"))
    if request.is_json:
        data = request.get_json()
    else:
        data = request.form
    
    # Get user_ids (can be single or list)
    user_ids = []
    if request.is_json:
        user_id = data.get("user_id")
        user_ids_list = data.get("user_ids", [])
        if user_id:
            user_ids = [int(user_id)]
        elif user_ids_list:
            user_ids = [int(uid) for uid in user_ids_list] if isinstance(user_ids_list, list) else []
        else:
            user_ids_str = data.get("user_ids", "")
            if isinstance(user_ids_str, str):
                user_ids = [int(uid.strip()) for uid in user_ids_str.split(",") if uid.strip()]
    else:
        user_id = data.get("user_id", type=int)
        user_ids_str = data.get("user_ids", "")
        if user_id:
            user_ids = [user_id]
        elif user_ids_str:
            user_ids = [int(uid.strip()) for uid in user_ids_str.split(",") if uid.strip()]
    
    role_id = data.get("role_id", type=int)
    is_temporary = data.get("is_temporary") == "true" or data.get("is_temporary") == True if not request.is_json else data.get("is_temporary", False)
    expiry_date_str = data.get("expiry_date") or data.get("role_expires_at", "")
    notes = data.get("notes", "").strip()
    requires_confirmation = data.get("requires_confirmation", False)
    
    if not user_ids:
        if request.is_json:
            return jsonify({"success": False, "message": "No users selected."}), 400
        flash("No users selected.", "danger")
        return redirect(url_for("admin.user_roles"))
    
    if not role_id:
        if request.is_json:
            return jsonify({"success": False, "message": "No role selected."}), 400
        flash("No role selected.", "danger")
        return redirect(url_for("admin.user_roles"))
    
    role = get_or_404(Role, role_id)
    
    # Check if assigning ADMIN role
    is_admin_role = role.name == "Admin" or role.name == "ADMIN"
    if is_admin_role and not requires_confirmation:
        if request.is_json:
            return jsonify({"success": False, "message": "Admin role assignment requires confirmation."}), 400
        flash("Admin role assignment requires confirmation.", "danger")
        return redirect(url_for("admin.user_roles"))
    
    # Parse expiry date if temporary
    expiry_date = None
    if is_temporary and expiry_date_str:
        try:
            expiry_date = datetime.strptime(expiry_date_str, "%Y-%m-%d")
        except ValueError:
            if request.is_json:
                return jsonify({"success": False, "message": "Invalid expiry date format."}), 400
            flash("Invalid expiry date format.", "danger")
            return redirect(url_for("admin.user_roles"))
    
    success_count = 0
    error_count = 0
    
    for user_id in user_ids:
        try:
            user = User.query.get(user_id)
            if not user:
                error_count += 1
                continue
            
            # Admin protection: Cannot remove admin role from current user
            if user.id == current_user.id and user.is_admin and not is_admin_role:
                error_count += 1
                continue
            
            # Admin protection: Cannot remove admin role from admin users
            if user.is_admin and not is_admin_role:
                error_count += 1
                continue
            
            old_role_id = user.role_id
            
            # If temporary role, save current role as previous
            if is_temporary and old_role_id != role_id:
                user.previous_role_id = old_role_id
            
            # Assign new role
            user.role_id = role_id
            user.is_temporary_role = is_temporary
            user.role_expiry_date = expiry_date
            user.role_expires_at = expiry_date  # Sync both fields
            db.session.flush()
            
            # Log the assignment
            log_role_assignment(
                admin_user_id=current_user.id,
                affected_user_id=user.id,
                old_role_id=old_role_id,
                new_role_id=role_id,
                is_bulk=len(user_ids) > 1,
                is_temporary=is_temporary,
                expiry_date=expiry_date,
                notes=notes
            )
            
            success_count += 1
        except Exception as e:
            from flask import current_app
            current_app.logger.exception(f"Error assigning role to user {user_id}: {e}")
            error_count += 1
    
    db.session.commit()
    
    if request.is_json or request.accept_mimetypes.accept_json:
        return jsonify({
            "success": True,
            "message": f"Role '{role.name}' assigned to {success_count} user(s).",
            "success_count": success_count,
            "error_count": error_count
        })
    
    if success_count > 0:
        flash(f"Role '{role.name}' assigned to {success_count} user(s).", "success")
    if error_count > 0:
        flash(f"Failed to assign role to {error_count} user(s). Some users may be protected.", "warning")
    
    return redirect(url_for("admin.user_roles"))


@admin_bp.route("/users/bulk-assign-role", methods=["POST"])
@admin_required
def bulk_assign_role():
    """Bulk assign role to multiple users."""
    if request.is_json:
        data = request.get_json()
    else:
        data = request.form
    
    # Handle both JSON and form data
    if request.is_json:
        user_ids_str = data.get("user_ids", "")
        is_temporary = data.get("is_temporary", False)
    else:
        user_ids_str = data.get("user_ids", "")
        is_temporary = data.get("is_temporary") == "true" or data.get("is_temporary") == True
    
    role_id = data.get("role_id", type=int)
    expiry_date_str = data.get("expiry_date", "")
    notes = data.get("notes", "").strip()
    
    # Parse user_ids from comma-separated string
    if isinstance(user_ids_str, str):
        try:
            user_ids = [int(uid.strip()) for uid in user_ids_str.split(",") if uid.strip()]
        except ValueError:
            user_ids = []
    elif isinstance(user_ids_str, list):
        user_ids = [int(uid) for uid in user_ids_str]
    else:
        user_ids = []
    
    if not user_ids:
        if request.is_json:
            return jsonify({"success": False, "message": "No users selected."}), 400
        flash("No users selected.", "danger")
        return redirect(url_for("admin.user_roles"))
    
    if not role_id:
        if request.is_json:
            return jsonify({"success": False, "message": "No role selected."}), 400
        flash("No role selected.", "danger")
        return redirect(url_for("admin.user_roles"))
    
    # Parse expiry date if temporary
    expiry_date = None
    if is_temporary and expiry_date_str:
        try:
            expiry_date = datetime.strptime(expiry_date_str, "%Y-%m-%d")
        except ValueError:
            if request.is_json:
                return jsonify({"success": False, "message": "Invalid expiry date format."}), 400
            flash("Invalid expiry date format.", "danger")
            return redirect(url_for("admin.user_roles"))
    
    role = get_or_404(Role, role_id)
    success_count = 0
    error_count = 0
    
    for user_id in user_ids:
        try:
            user = User.query.get(user_id)
            if not user:
                error_count += 1
                continue
            
            # Admin role protection
            if user.is_admin and role.name != 'Admin':
                error_count += 1
                continue
            
            # Prevent removing admin role from current user
            if user.id == current_user.id and user.is_admin and role.name != 'Admin':
                error_count += 1
                continue
            
            old_role_id = user.role_id
            
            # Store previous role if changing
            if old_role_id != role_id:
                user.previous_role_id = old_role_id
            
            user.role_id = role_id
            user.is_temporary_role = is_temporary
            user.role_expiry_date = expiry_date
            user.role_expires_at = expiry_date  # Sync both fields
            db.session.flush()
            
            # Log the assignment
            log_role_assignment(
                admin_user_id=current_user.id,
                affected_user_id=user.id,
                old_role_id=old_role_id,
                new_role_id=role_id,
                is_bulk=True,
                is_temporary=is_temporary,
                expiry_date=expiry_date,
                notes=notes
            )
            
            success_count += 1
        except Exception as e:
            from flask import current_app
            current_app.logger.exception(f"Error assigning role to user {user_id}: {e}")
            error_count += 1
    
    db.session.commit()
    
    # Return JSON for AJAX requests, otherwise redirect with flash messages
    if request.is_json or request.accept_mimetypes.accept_json:
        return jsonify({
            "success": True,
            "message": f"Role '{role.name}' assigned to {success_count} user(s).",
            "success_count": success_count,
            "error_count": error_count
        })
    
    if success_count > 0:
        flash(f"Role '{role.name}' assigned to {success_count} user(s).", "success")
    if error_count > 0:
        flash(f"Failed to assign role to {error_count} user(s). Some users may be protected.", "warning")
    
    return redirect(url_for("admin.user_roles"))


@admin_bp.route("/role-assignment-logs")
@admin_required
def role_assignment_logs():
    """View role assignment audit logs."""
    try:
        logs = RoleAssignmentLog.query.order_by(RoleAssignmentLog.created_at.desc()).limit(100).all()
        
        # Filter options
        user_filter = request.args.get("user_id", type=int)
        role_filter = request.args.get("role_id", type=int)
        date_filter = request.args.get("date", "")
        
        query = RoleAssignmentLog.query
        
        if user_filter:
            query = query.filter(RoleAssignmentLog.affected_user_id == user_filter)
        if role_filter:
            query = query.filter(RoleAssignmentLog.new_role_id == role_filter)
        if date_filter:
            try:
                filter_date = datetime.strptime(date_filter, "%Y-%m-%d").date()
                query = query.filter(func.date(RoleAssignmentLog.created_at) == filter_date)
            except ValueError:
                pass
        
        logs = query.order_by(RoleAssignmentLog.created_at.desc()).limit(200).all()
        users = User.query.order_by(User.email.asc()).all()
        roles = Role.query.order_by(Role.name.asc()).all()
        
        return render_template("admin/role_assignment_logs.html", logs=logs, users=users, roles=roles)
    except Exception as e:
        from flask import current_app
        current_app.logger.exception(f"Error loading role assignment logs: {e}")
        flash("Error loading role assignment logs.", "danger")
        return render_template("admin/role_assignment_logs.html", logs=[], users=[], roles=[])


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
    departments = Department.query.order_by(Department.name.asc()).all()
    
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        role_ids = request.form.getlist("role_ids")  # Multiple roles
        legacy_role = request.form.get("legacy_role", "")
        department_id = request.form.get("department_id")
        
        # Validate email
        if not email or "@" not in email:
            flash("Please provide a valid email address.", "danger")
            return render_template("admin/user_form.html", action="Add", user=None, roles=roles, departments=departments)
        
        # Check if user already exists
        existing_user = User.query.filter(func.lower(User.email) == email).first()
        if existing_user:
            flash(f"User with email '{email}' already exists.", "danger")
            return render_template("admin/user_form.html", action="Add", user=None, roles=roles, departments=departments)
        
        # Generate secure password using production password generator
        import secrets
        import string
        generated_password = "".join(secrets.choice(string.ascii_letters + string.digits + "!@#$%^&*") for _ in range(12))
        temp_password = generated_password
        
        # Create user
        user = User(
            email=email,
            must_change_password=True,
            force_password_change=True,  # Legacy compatibility
            first_login=True  # Require password change on first login
        )
        
        # Set legacy role if provided (for backward compatibility)
        if legacy_role:
            try:
                user.role = UserRole[legacy_role]
            except (KeyError, ValueError):
                pass
        
        # Set the auto-generated password with 24-hour expiry
        user.set_password(temp_password, is_temporary=True)
        
        db.session.add(user)
        db.session.flush()  # Flush to get user.id
        
        # Assign multiple roles
        for role_id_str in role_ids:
            try:
                role_id = int(role_id_str)
                role = db.session.get(Role, role_id)
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
        
        # Create employee record if department is selected
        if department_id:
            from sas_management.models import Employee
            try:
                emp = Employee(
                    user_id=user.id,
                    department_id=int(department_id),
                    first_name=email.split('@')[0],
                    last_name='',
                    email=email
                )
                db.session.add(emp)
            except (ValueError, TypeError):
                pass
        
        db.session.commit()
        
        # Flash message with the temporary password
        flash(f"User '{email}' created successfully! Temporary password: {temp_password} (expires in 24 hours)", "success")
        return redirect(url_for("admin.users_list"))
    
    return render_template("admin/user_form.html", action="Add", user=None, roles=roles, departments=departments)


@admin_bp.route("/users/<int:user_id>/edit", methods=["GET", "POST"])
@admin_required
def users_edit(user_id):
    """Edit a user."""
    user = get_or_404(User, user_id)
    roles = Role.query.order_by(Role.name.asc()).all()
    departments = Department.query.order_by(Department.name.asc()).all()
    
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        role_ids = request.form.getlist("role_ids")  # Multiple roles
        legacy_role = request.form.get("legacy_role", "")
        must_change_password = request.form.get("must_change_password") == "on"
        department_id = request.form.get("department_id")
        
        # Validate email
        if not email or "@" not in email:
            flash("Please provide a valid email address.", "danger")
            return render_template("admin/user_form.html", action="Edit", user=user, roles=roles, departments=departments)
        
        # Check if email is already taken by another user
        existing_user = User.query.filter(
            func.lower(User.email) == email,
            User.id != user_id
        ).first()
        if existing_user:
            flash(f"User with email '{email}' already exists.", "danger")
            return render_template("admin/user_form.html", action="Edit", user=user, roles=roles, departments=departments)
        
        temp_password = request.form.get("temp_password", "").strip()
        
        user.email = email
        user.must_change_password = must_change_password
        user.force_password_change = must_change_password  # Legacy compatibility
        
        # Handle temporary password if provided
        if temp_password:
            user.set_password(temp_password, is_temporary=True)
            user.force_password_change = True
            user.first_login = True
            user.must_change_password = True
            flash(f"Password has been reset to a temporary password for user '{email}'. Temporary password: {temp_password} (expires in 24 hours)", "success")
        
        # Admin role protection: Prevent removing or downgrading Admin role
        was_admin = user.is_admin
        if was_admin:
            # Check if Admin role is being removed
            admin_role = Role.query.filter_by(name='Admin').first()
            admin_role_id = admin_role.id if admin_role else None
            
            # Check if Admin role is in the new role_ids
            has_admin_role = False
            for role_id_str in role_ids:
                try:
                    if int(role_id_str) == admin_role_id:
                        has_admin_role = True
                        break
                except (ValueError, TypeError):
                    continue
            
            # Also check legacy_role
            if legacy_role == 'Admin':
                has_admin_role = True
            
            if not has_admin_role:
                flash("Cannot remove Admin role from a user. Admin role cannot be downgraded.", "danger")
                return render_template("admin/user_form.html", action="Edit", user=user, roles=roles, departments=departments)
        
        # Update roles (many-to-many)
        # Need to properly clear dynamic relationship
        for role in list(user.roles.all()):
            user.roles.remove(role)
        for role_id_str in role_ids:
            try:
                role_id = int(role_id_str)
                role = db.session.get(Role, role_id)
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
                # Ensure Admin role is preserved if user was admin
                if was_admin and legacy_role != 'Admin':
                    flash("Cannot downgrade Admin role. Admin users must retain Admin role.", "danger")
                    return render_template("admin/user_form.html", action="Edit", user=user, roles=roles, departments=departments)
            except (KeyError, ValueError):
                pass
        
        # Update employee department if selected
        if department_id:
            from sas_management.models import Employee
            emp = Employee.query.filter_by(user_id=user.id).first()
            if emp:
                emp.department_id = int(department_id)
            else:
                emp = Employee(
                    user_id=user.id,
                    department_id=int(department_id),
                    first_name=user.email.split('@')[0],
                    last_name='',
                    email=user.email
                )
                db.session.add(emp)
        elif department_id == '':
            from sas_management.models import Employee
            emp = Employee.query.filter_by(user_id=user.id).first()
            if emp:
                emp.department_id = None
        
        db.session.commit()
        flash(f"User '{email}' updated successfully.", "success")
        return redirect(url_for("admin.users_list"))
    
    return render_template("admin/user_form.html", action="Edit", user=user, roles=roles, departments=departments)


@admin_bp.route("/users/<int:user_id>/reset-password", methods=["POST"])
@admin_required
def users_reset_password(user_id):
    """Reset a user's password and generate a new temporary password."""
    user = get_or_404(User, user_id)
    
    # Generate new secure password with 24-hour expiry
    temp_password = generate_secure_password(12)
    user.set_password(temp_password, is_temporary=True)
    user.force_password_change = True
    user.first_login = True  # Require password change on next login
    user.must_change_password = True
    db.session.commit()
    
    flash(f"Password reset for '{user.email}'. New temporary password: {temp_password} (expires in 24 hours)", "success")
    return redirect(url_for("admin.users_list"))


@admin_bp.route("/users/<int:user_id>/delete", methods=["POST"])
@admin_required
def users_delete(user_id):
    """Delete a user."""
    user = get_or_404(User, user_id)
    
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
                role = db.session.get(Role, role_id)
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
    group = get_or_404(Group, group_id)
    
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
                role = db.session.get(Role, role_id)
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
    group = get_or_404(Group, group_id)
    
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
    group = get_or_404(Group, group_id)
    
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

# ============================================================================
# QUICK ACTION ALIASES (for stable endpoints used by templates)
# ============================================================================

# /admin/roles → admin.manage_roles (alias to roles_list)
admin_bp.add_url_rule("/roles", endpoint="manage_roles", view_func=roles_list)

# /admin/permissions → admin.view_permissions (alias to permissions_list)
admin_bp.add_url_rule("/permissions", endpoint="view_permissions", view_func=permissions_list)

# /admin/users → admin.manage_users (alias to users_list)
admin_bp.add_url_rule("/users", endpoint="manage_users", view_func=users_list)


@admin_bp.route("/assign-roles", methods=["GET", "POST"])
@login_required
def assign_roles():
    """
    Simple role assignment interface for single users.
    
    GET:  Render admin/assign_roles.html with all users and roles.
    POST: Assign role_id to user_id with Admin self-protection.
    """
    # Basic admin gate: allow first user, super admin, or admin role
    try:
        is_first_user = getattr(current_user, "id", None) == 1
        is_super_admin = hasattr(current_user, "is_super_admin") and current_user.is_super_admin()
        is_admin_role = hasattr(current_user, "is_admin") and current_user.is_admin
        if not (is_first_user or is_super_admin or is_admin_role):
            flash("Admin access is required to manage roles.", "danger")
            return redirect(url_for("core.dashboard"))
    except Exception:
        flash("Admin access is required to manage roles.", "danger")
        return redirect(url_for("core.dashboard"))

    users = User.query.order_by(User.email.asc()).all()
    roles = Role.query.order_by(Role.name.asc()).all()

    generated_password = None
    assigned_email = None

    if request.method == "POST":
        user_id = request.form.get("user_id", type=int)
        role_id = request.form.get("role_id", type=int)
        set_temporary_password = request.form.get("set_temporary_password") == "on"
        generate_password = request.form.get("generate_password") == "on"
        temp_password = request.form.get("temp_password", "").strip()

        if not user_id or not role_id:
            flash("Both user and role are required.", "danger")
            return redirect(url_for("admin.assign_roles"))

        user = db.session.get(User, user_id)
        if not user:
            flash("Selected user was not found.", "danger")
            return redirect(url_for("admin.assign_roles"))

        role = db.session.get(Role, role_id)
        if not role:
            flash("Selected role was not found.", "danger")
            return redirect(url_for("admin.assign_roles"))

        # Prevent removing or downgrading ADMIN from self
        try:
            if user.id == current_user.id and user.is_admin:
                if role.name.lower() != "admin":
                    flash("You cannot remove or downgrade your own ADMIN role.", "danger")
                    return redirect(url_for("admin.assign_roles"))
        except Exception:
            # If we cannot determine admin status safely, fall back to allowing assignment
            pass

        # Handle temporary password
        if set_temporary_password:
            if generate_password:
                import secrets
                import string
                generated_password = "".join(secrets.choice(string.ascii_letters + string.digits + "!@#$%^&*") for _ in range(12))
                temp_password = generated_password
            elif temp_password:
                generated_password = temp_password
            
            if generated_password:
                user.set_password(generated_password, is_temporary=True)
                user.must_change_password = True
                user.force_password_change = True
                assigned_email = user.email

        # Perform assignment
        old_role_id = user.role_id
        user.role_id = role.id

        try:
            db.session.commit()
        except Exception as e:
            from flask import current_app
            current_app.logger.exception(f"Error assigning role: {e}")
            db.session.rollback()
            flash("An error occurred while assigning the role.", "danger")
            return redirect(url_for("admin.assign_roles"))

        if generated_password:
            flash(f"Role '{role.name}' assigned to {user.email}. Temporary password generated (expires in 24 hours).", "success")
        else:
            flash(f"Role '{role.name}' assigned to {user.email}.", "success")
        
        return render_template(
            "admin/assign_roles.html",
            users=users,
            roles=roles,
            current_user=current_user,
            generated_password=generated_password,
            assigned_email=assigned_email,
        )

    return render_template(
        "admin/assign_roles.html",
        users=users,
        roles=roles,
        current_user=current_user,
    )

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


@admin_bp.route("/ai-features/toggle/<int:feature_id>", methods=["POST"])
@admin_required
def toggle_ai_feature(feature_id):
    """
    Toggle a SAS AI feature on/off from the admin panel.

    This is a thin admin wrapper around the SAS AI feature state
    that operates on a stable integer feature_id mapped from the
    canonical AI feature registry.
    """
    from sas_management.ai.registry import FEATURE_DEFINITIONS, get_feature_by_key
    from sas_management.ai.state import is_enabled as is_feature_enabled, enable, disable

    try:
        # Map numeric feature_id to feature_key using registry definition order (1-based)
        feature_keys = list(FEATURE_DEFINITIONS.keys())
        if feature_id < 1 or feature_id > len(feature_keys):
            return jsonify({"success": False, "error": "Feature not found"}), 404

        feature_key = feature_keys[feature_id - 1]
        feature = get_feature_by_key(feature_key)
        if not feature:
            return jsonify({"success": False, "error": "Feature not found"}), 404

        currently_enabled = is_feature_enabled(feature_key)

        # Flip runtime state
        if currently_enabled:
            success = disable(feature_key)
        else:
            success = enable(feature_key)

        if not success:
            return jsonify({"success": False, "error": "Unable to update feature state"}), 400

        # No DB row is mutated, but commit any pending changes to be safe
        try:
            db.session.commit()
        except Exception:
            db.session.rollback()

        return jsonify({
            "success": True,
            "is_enabled": not currently_enabled,
            "feature_id": feature_id,
            "feature_key": feature_key,
        }), 200
    except Exception as e:
        from flask import current_app
        current_app.logger.exception(f"Error toggling AI feature (id={feature_id}): {e}")
        return jsonify({"success": False, "error": "Internal server error"}), 500


# ============================================================================
# DEPARTMENT MANAGEMENT ROUTES
# ============================================================================

@admin_bp.route("/departments")
@admin_required
def departments_list():
    """List all departments with user counts."""
    try:
        departments = Department.query.order_by(Department.name.asc()).all()
        from sas_management.models import Employee
        dept_with_counts = []
        for dept in departments:
            user_count = Employee.query.filter_by(department_id=dept.id).count()
            dept_with_counts.append({
                'department': dept,
                'user_count': user_count,
                'manager': dept.manager.email if dept.manager else None
            })
        return render_template("admin/departments_list.html", departments=dept_with_counts)
    except Exception as e:
        from flask import current_app
        current_app.logger.exception(f"Error loading departments: {e}")
        flash("Error loading departments.", "danger")
        return render_template("admin/departments_list.html", departments=[])


@admin_bp.route("/departments/add", methods=["GET", "POST"])
@admin_required
def departments_add():
    """Create a new department."""
    users = User.query.order_by(User.email.asc()).all()
    
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        description = request.form.get("description", "").strip()
        manager_id = request.form.get("manager_id")
        
        if not name:
            flash("Department name is required.", "danger")
            return render_template("admin/department_form.html", action="Add", department=None, users=users)
        
        existing = Department.query.filter(func.lower(Department.name) == name.lower()).first()
        if existing:
            flash(f"Department '{name}' already exists.", "danger")
            return render_template("admin/department_form.html", action="Add", department=None, users=users)
        
        dept = Department(
            name=name,
            description=description,
            manager_id=int(manager_id) if manager_id else None
        )
        db.session.add(dept)
        db.session.commit()
        flash(f"Department '{name}' created successfully!", "success")
        return redirect(url_for("admin.departments_list"))
    
    return render_template("admin/department_form.html", action="Add", department=None, users=users)


@admin_bp.route("/departments/<int:dept_id>/edit", methods=["GET", "POST"])
@admin_required
def departments_edit(dept_id):
    """Edit a department."""
    dept = get_or_404(Department, dept_id)
    users = User.query.order_by(User.email.asc()).all()
    
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        description = request.form.get("description", "").strip()
        manager_id = request.form.get("manager_id")
        
        if not name:
            flash("Department name is required.", "danger")
            return render_template("admin/department_form.html", action="Edit", department=dept, users=users)
        
        existing = Department.query.filter(
            func.lower(Department.name) == name.lower(),
            Department.id != dept_id
        ).first()
        if existing:
            flash(f"Department '{name}' already exists.", "danger")
            return render_template("admin/department_form.html", action="Edit", department=dept, users=users)
        
        dept.name = name
        dept.description = description
        dept.manager_id = int(manager_id) if manager_id else None
        db.session.commit()
        flash(f"Department '{name}' updated successfully!", "success")
        return redirect(url_for("admin.departments_list"))
    
    return render_template("admin/department_form.html", action="Edit", department=dept, users=users)


@admin_bp.route("/departments/<int:dept_id>/delete", methods=["POST"])
@admin_required
def departments_delete(dept_id):
    """Delete a department."""
    dept = get_or_404(Department, dept_id)
    
    if dept.employees:
        flash(f"Cannot delete department '{dept.name}' - it has employees assigned.", "danger")
        return redirect(url_for("admin.departments_list"))
    
    dept_name = dept.name
    db.session.delete(dept)
    db.session.commit()
    flash(f"Department '{dept_name}' deleted successfully!", "success")
    return redirect(url_for("admin.departments_list"))


@admin_bp.route("/departments/<int:dept_id>/users")
@admin_required
def departments_users(dept_id):
    """View users/employees in a specific department."""
    dept = get_or_404(Department, dept_id)
    employees = Employee.query.filter_by(department_id=dept_id).all()
    return render_template("admin/department_users.html", department=dept, employees=employees)


# ============================================================================
# USER MANAGEMENT BY DEPARTMENT
# ============================================================================

@admin_bp.route("/users/by-department")
@admin_required
def users_by_department():
    """View all users grouped by department."""
    departments = Department.query.order_by(Department.name.asc()).all()
    users = User.query.order_by(User.email.asc()).all()
    
    from sas_management.models import Employee
    users_by_dept = {}
    for dept in departments:
        users_in_dept = []
        for user in users:
            emp = Employee.query.filter_by(user_id=user.id, department_id=dept.id).first()
            if emp:
                users_in_dept.append({
                    'user': user,
                    'employee': emp,
                    'position': emp.position_obj.title if emp.position_obj else emp.position
                })
        if users_in_dept:
            users_by_dept[dept.id] = {
                'department': dept,
                'users': users_in_dept,
                'count': len(users_in_dept)
            }
    
    users_without_dept = [u for u in users if not Employee.query.filter_by(user_id=u.id).first()]
    
    return render_template("admin/users_by_department.html", 
                           users_by_dept=users_by_dept,
                           users_without_dept=users_without_dept,
                           departments=departments)

