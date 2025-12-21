"""
AI Module Permissions

Access control for AI features. All AI features require appropriate role permissions.
"""
from flask_login import current_user
from sas_management.models import UserRole


# Canonical AI permission types
AI_PERMISSIONS = {
    "ai_chat": "Use AI chat",
    "ai_actions": "Generate AI reports & summaries",
    "ai_analytics": "Explain analytics & KPIs",
    "ai_voice": "Use voice input/output",
    "ai_memory": "Allow AI to remember preferences",
    "ai_scheduling": "Schedule AI reports",
}


def check_ai_access():
    """
    Check if current user has access to AI features.
    Admin users always have access.
    
    Returns:
        True if user has access, False otherwise
    """
    if not current_user or not current_user.is_authenticated:
        return False
    
    # Admin bypass: If user is Admin, grant access immediately
    if hasattr(current_user, 'is_admin') and current_user.is_admin:
        return True
    
    # AI features are available to Admin and SalesManager roles
    # Can be extended based on specific feature requirements
    return current_user.role in [UserRole.Admin, UserRole.SalesManager]


def require_ai_access(f):
    """
    Decorator to require AI access for a route.
    Admin users bypass all checks and are always allowed.
    
    Usage:
        @require_ai_access
        def my_ai_route():
            ...
    """
    from functools import wraps
    
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Admin bypass: If user is Admin, allow access immediately
        if current_user.is_authenticated and hasattr(current_user, 'is_admin') and current_user.is_admin:
            return f(*args, **kwargs)
        if not check_ai_access():
            from flask import abort
            abort(403)
        return f(*args, **kwargs)
    
    return decorated_function

