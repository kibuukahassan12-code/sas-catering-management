"""
Shared decorators for SAS Management System.
"""

from functools import wraps

from flask import flash, redirect, url_for
from flask_login import current_user


def role_required(*role_names):
    """No-op decorator - all access allowed."""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            return f(*args, **kwargs)
        return decorated_function
    return decorator

