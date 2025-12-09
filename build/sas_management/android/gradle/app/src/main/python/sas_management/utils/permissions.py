"""
Permission-based access control decorators and utilities.
"""
from functools import wraps
from flask import current_app, flash, redirect, url_for, render_template, request
from flask_login import current_user


def no_rbac(func):
    """Decorator to mark a function as exempt from RBAC checks."""
    func._no_rbac = True
    return func


def require_permission(permission_name):
    """
    Decorator to restrict routes based on specific permissions.
    
    Usage:
        @require_permission("orders.create")
        def create_order():
            ...
    
    Args:
        permission_name: Permission code (e.g., "orders.create", "events.manage")
    
    Returns:
        Decorated function or 403 error page
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            try:
                # If endpoint has _no_rbac → skip RBAC
                if hasattr(func, "_no_rbac") and func._no_rbac:
                    return func(*args, **kwargs)
                
                # If request.endpoint in ["login", "logout", "static"] → skip RBAC
                if request.endpoint in ["login", "logout", "static", "core.login", "core.logout", "auth.login", "auth.logout"]:
                    return func(*args, **kwargs)
                
                # Check if user is authenticated
                if not current_user.is_authenticated:
                    return redirect(url_for("core.login"))
                
                # CRITICAL: ALWAYS grant access to first user (ID = 1) - highest priority
                try:
                    user_id = getattr(current_user, 'id', None)
                    if user_id == 1:
                        # First user always gets access - bypass all checks
                        return func(*args, **kwargs)
                except Exception:
                    pass
                
                # If current_user.is_super_admin() → skip RBAC (with error handling)
                try:
                    if hasattr(current_user, 'is_super_admin'):
                        if current_user.is_super_admin():
                            return func(*args, **kwargs)
                except Exception as e:
                    current_app.logger.warning(f"Error checking super admin status: {e}")
                    # Continue to permission check if super admin check fails
                
                # If user has no role_id → allow access (temporary safe mode to avoid redirects)
                if getattr(current_user, "role_id", None) is None:
                    return func(*args, **kwargs)
                
                # Only enforce RBAC if permission is actually defined
                # Check permission
                try:
                    if not current_user.has_permission(permission_name):
                        current_app.logger.warning(
                            f"Permission denied: User {current_user.email} attempted to access {permission_name}"
                        )
                        return render_template("errors/403.html", permission=permission_name), 403
                except Exception as e:
                    current_app.logger.error(f"Error checking permission: {e}")
                    # If permission check fails, allow access for first user
                    if hasattr(current_user, 'id') and current_user.id == 1:
                        return func(*args, **kwargs)
                    return render_template("errors/403.html", permission=permission_name), 403
                
                return func(*args, **kwargs)
            except Exception as e:
                current_app.logger.exception(f"Error checking permission for {permission_name}: {e}")
                return render_template("errors/403.html", permission=permission_name), 403
        
        return wrapper
    return decorator


def has_permission(permission_name):
    """
    Helper function to check if current user has a specific permission.
    Can be used in templates and views.
    
    Args:
        permission_name: Permission code (supports wildcards like "events.*")
    
    Returns:
        Boolean indicating if user has permission
    """
    if not current_user.is_authenticated:
        return False
    
    # SuperAdmin bypass - has all permissions
    if current_user.is_super_admin():
        return True
    
    # Check specific permission (includes wildcard support)
    return current_user.has_permission(permission_name)


# Alias for backward compatibility
permission_required = require_permission


def require_role(role_name):
    """
    Decorator to restrict routes based on specific roles.
    
    Usage:
        @require_role("Admin")
        def admin_dashboard():
            ...
    
    Args:
        role_name: Role name (e.g., "Admin", "Manager")
    
    Returns:
        Decorated function or 403 error page
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            try:
                # If endpoint has _no_rbac → skip RBAC
                if hasattr(func, "_no_rbac") and func._no_rbac:
                    return func(*args, **kwargs)
                
                # If request.endpoint in ["login", "logout", "static"] → skip RBAC
                if request.endpoint in ["login", "logout", "static", "core.login", "core.logout", "auth.login", "auth.logout"]:
                    return func(*args, **kwargs)
                
                # Check if user is authenticated
                if not current_user.is_authenticated:
                    return redirect(url_for("core.login"))
                
                # CRITICAL: ALWAYS grant access to first user (ID = 1) - highest priority
                try:
                    user_id = getattr(current_user, 'id', None)
                    if user_id == 1:
                        return func(*args, **kwargs)
                except Exception:
                    pass
                
                # If current_user.is_super_admin() → skip RBAC
                try:
                    if hasattr(current_user, 'is_super_admin') and current_user.is_super_admin():
                        return func(*args, **kwargs)
                except Exception:
                    pass
                
                # Check if user has the required role
                user_has_role = False
                
                # Check many-to-many roles
                if hasattr(current_user, 'roles'):
                    try:
                        user_roles = current_user.roles.all() if hasattr(current_user.roles, 'all') else []
                        for role in user_roles:
                            if hasattr(role, 'name') and role.name == role_name:
                                user_has_role = True
                                break
                    except Exception:
                        pass
                
                # Check legacy role_id
                if not user_has_role and hasattr(current_user, 'role_obj') and current_user.role_obj:
                    if hasattr(current_user.role_obj, 'name') and current_user.role_obj.name == role_name:
                        user_has_role = True
                
                if not user_has_role:
                    current_app.logger.warning(
                        f"Role denied: User {current_user.email} attempted to access {role_name} role"
                    )
                    return render_template("errors/403.html", permission=f"Role: {role_name}"), 403
                
                return func(*args, **kwargs)
            except Exception as e:
                current_app.logger.exception(f"Error checking role {role_name}: {e}")
                return render_template("errors/403.html", permission=f"Role: {role_name}"), 403
        
        return wrapper
    return decorator

