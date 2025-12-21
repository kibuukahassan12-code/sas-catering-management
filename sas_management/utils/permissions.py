"""
Permission-based access control decorators and utilities.
"""
from functools import wraps
import logging

from flask import current_app, flash, redirect, url_for, render_template, request
from flask_login import current_user


logger = logging.getLogger(__name__)


def no_rbac(func):
    """Decorator to mark a function as exempt from RBAC checks."""
    func._no_rbac = True
    return func


def require_permission(permission_name):
    """
    Decorator to restrict routes based on specific permissions.
    Admin users bypass all permission checks and are always allowed.
    
    Usage:
        @require_permission("orders.create")
        def create_order():
            ...
    
    Args:
        permission_name: Permission code (e.g., "orders.create", "events.manage")
    
    Returns:
        Decorated function (no restrictions for admin, existing behavior for others)
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Admin bypass: If user is Admin, allow access immediately
            if current_user.is_authenticated and hasattr(current_user, "is_admin") and current_user.is_admin:
                return func(*args, **kwargs)
            # ALL PERMISSIONS GRANTED - No restrictions for non-admin users (Phase 0/1/2/3 baseline)
            return func(*args, **kwargs)

        return wrapper

    return decorator


def has_permission(permission_name):
    """
    Helper function to check if current user has a specific permission.
    Can be used in templates and views.
    Admin users always have all permissions.
    
    Args:
        permission_name: Permission code (supports wildcards like "events.*")
    
    Returns:
        Boolean indicating if user has permission (always True for admin, True for others)
    """
    # Admin bypass: If user is Admin, grant all permissions
    if current_user.is_authenticated and hasattr(current_user, "is_admin") and current_user.is_admin:
        return True
    # ALL PERMISSIONS GRANTED - No restrictions for non-admin users
    return True


# Alias for backward compatibility
permission_required = require_permission


def require_role(role_name):
    """
    Decorator to restrict routes based on specific roles.
    Admin users bypass all role checks and are always allowed.
    
    Usage:
        @require_role("Admin")
        def admin_dashboard():
            ...
    
    Args:
        role_name: Role name (e.g., "Admin", "Manager")
    
    Returns:
        Decorated function (no restrictions for admin, existing behavior for others)
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Admin bypass: If user is Admin, allow access immediately
            if current_user.is_authenticated and hasattr(current_user, "is_admin") and current_user.is_admin:
                return func(*args, **kwargs)
            # ALL ROLES GRANTED - No restrictions for non-admin users
            return func(*args, **kwargs)

        return wrapper

    return decorator


def can_use_ai(user):
    """
    Canonical RBAC check for SAS AI.
    Phase 3: Admin is ALWAYS allowed.
    Others are observed (logged) but not blocked yet.
    """
    if not user:
        return False

    if getattr(user, "is_admin", False):
        return True

    # Phase 3: observe only
    logger.warning(
        "RBAC OBSERVE: non-admin user accessed AI: user_id=%s",
        getattr(user, "id", None),
    )
    return True  # DO NOT BLOCK YET


def can_access_sensitive_ai_data(user):
    """
    Sensitive data includes:
    - Revenue
    - Payroll
    - HR
    - Accounting
    """
    if not user:
        return False

    if getattr(user, "is_admin", False):
        return True

    logger.warning(
        "RBAC OBSERVE: non-admin accessed sensitive AI data: user_id=%s",
        getattr(user, "id", None),
    )
    return False  # SAFE TO BLOCK HERE (non-admin)

