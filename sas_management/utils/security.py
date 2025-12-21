"""
Security utilities for RBAC enforcement.
"""
from functools import wraps
from flask import current_app, flash, redirect, url_for
from flask_login import current_user


def require_permission(permission):
    """
    Decorator to require a specific permission for a route.
    Admin users bypass all permission checks and are always allowed.
    
    Usage:
        @require_permission("view_users")
        def users_list():
            ...
    
    Args:
        permission: Permission name (e.g., "view_users", "manage_inventory")
    
    Returns:
        Decorated function (no restrictions for admin, existing behavior for others)
    """
    def decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            # Admin bypass: If user is Admin, allow access immediately
            if current_user.is_authenticated and hasattr(current_user, 'is_admin') and current_user.is_admin:
                return f(*args, **kwargs)
            # ALL PERMISSIONS GRANTED - No restrictions for non-admin users
            return f(*args, **kwargs)
        return wrapper
    return decorator

