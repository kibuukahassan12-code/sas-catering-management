"""
Shared decorators for SAS Management System.
"""

from functools import wraps

from flask import flash, redirect, url_for
from flask_login import current_user


def role_required(*role_names):
    """
    Decorator to require specific roles.
    Admin users bypass all role checks and are always allowed.
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # Admin bypass: If user is Admin, allow access immediately
            if current_user.is_authenticated and hasattr(current_user, 'is_admin') and current_user.is_admin:
                return f(*args, **kwargs)
            # For non-admin users, allow all access (existing behavior)
            return f(*args, **kwargs)
        return decorated_function
    return decorator

