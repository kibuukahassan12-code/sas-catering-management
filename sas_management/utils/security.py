"""
Security utilities for RBAC enforcement.
"""
from functools import wraps
from flask import current_app, flash, redirect, url_for
from flask_login import current_user


def require_permission(permission):
    """
    Decorator to require a specific permission for a route.
    DISABLED: All permissions now granted to all users.
    
    Usage:
        @require_permission("view_users")
        def users_list():
            ...
    
    Args:
        permission: Permission name (e.g., "view_users", "manage_inventory")
    
    Returns:
        Decorated function (no restrictions)
    """
    def decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            # ALL PERMISSIONS GRANTED - No restrictions
            return f(*args, **kwargs)
        return wrapper
    return decorator

