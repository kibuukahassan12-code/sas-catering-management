"""
Security utilities for RBAC enforcement.
"""
from functools import wraps
from flask import current_app, flash, redirect, url_for
from flask_login import current_user


def require_permission(permission):
    """
    Decorator to require a specific permission for a route.
    
    Usage:
        @require_permission("view_users")
        def users_list():
            ...
    
    Args:
        permission: Permission name (e.g., "view_users", "manage_inventory")
    
    Returns:
        Decorated function or redirect to dashboard
    """
    def decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            if not current_user.is_authenticated:
                flash("Please log in to access this resource.", "warning")
                return redirect(url_for("core.login"))
            
            # Super Admin bypass
            if current_user.is_super_admin():
                return f(*args, **kwargs)
            
            if not current_user.has_permission(permission):
                flash("Access denied.", "danger")
                return redirect(url_for("core.dashboard"))
            
            return f(*args, **kwargs)
        return wrapper
    return decorator

