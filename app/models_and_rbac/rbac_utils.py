from functools import wraps
from flask import abort, flash, redirect, url_for
from flask_login import current_user

def permission_required(permission_name):
    """Decorator to require a specific permission."""
    def decorator(f):
        @wraps(f)
        def wrapped(*args, **kwargs):
            user = getattr(current_user, "_get_current_object", lambda: current_user)()
            
            if not user.is_authenticated:
                flash("Please log in to access this resource.", "warning")
                return redirect(url_for("core.login"))
            
            # Check if user has the required permission
            # Check role_obj (new RBAC system)
            if hasattr(user, 'role_obj') and user.role_obj:
                user_perms = {p.name for p in getattr(user.role_obj, "permissions", [])}
                if permission_name in user_perms:
                    return f(*args, **kwargs)
            
            # Fallback: check legacy role enum
            from models import UserRole
            if hasattr(user, 'role') and user.role == UserRole.Admin:
                return f(*args, **kwargs)
            
            # Check roles relationship if exists
            user_perms = set()
            if hasattr(user, "roles"):
                for role in getattr(user, "roles", []):
                    for p in getattr(role, "permissions", []):
                        user_perms.add(p.name)
            
            if permission_name not in user_perms:
                flash("You do not have permission to access this resource.", "danger")
                abort(403)
            
            return f(*args, **kwargs)
        return wrapped
    return decorator

