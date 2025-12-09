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
    DISABLED: All permissions now granted to all users.
    
    Usage:
        @require_permission("orders.create")
        def create_order():
            ...
    
    Args:
        permission_name: Permission code (e.g., "orders.create", "events.manage")
    
    Returns:
        Decorated function (no restrictions)
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # ALL PERMISSIONS GRANTED - No restrictions
            return func(*args, **kwargs)
        return wrapper
    return decorator


def has_permission(permission_name):
    """
    Helper function to check if current user has a specific permission.
    Can be used in templates and views.
    DISABLED: All permissions now granted to all users.
    
    Args:
        permission_name: Permission code (supports wildcards like "events.*")
    
    Returns:
        Boolean indicating if user has permission (always True)
    """
    # ALL PERMISSIONS GRANTED - No restrictions
    return True


# Alias for backward compatibility
permission_required = require_permission


def require_role(role_name):
    """
    Decorator to restrict routes based on specific roles.
    DISABLED: All roles now granted to all users.
    
    Usage:
        @require_role("Admin")
        def admin_dashboard():
            ...
    
    Args:
        role_name: Role name (e.g., "Admin", "Manager")
    
    Returns:
        Decorated function (no restrictions)
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # ALL ROLES GRANTED - No restrictions
            return func(*args, **kwargs)
        return wrapper
    return decorator

