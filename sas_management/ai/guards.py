"""
AI Feature Guards

HARD runtime guards to ensure features are enabled before execution.
Prevents errors and provides friendly messages when features are disabled.
"""
from functools import wraps
from flask import abort, jsonify, current_app, request, render_template
from flask_login import current_user
from sas_management.ai.state import is_enabled as check_feature_enabled
from sas_management.ai.registry import get_feature_by_key


def require_ai_feature(feature_key: str):
    """
    HARD runtime guard decorator to require an AI feature to be enabled.
    
    If feature is disabled:
    - For JSON/API requests: returns HTTP 403 with {"enabled": False, "error": "..."}
    - For HTML requests: renders branded "Feature Disabled" page
    
    Usage:
        @require_ai_feature("event_planner")
        def my_route():
            ...
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # Check if AI module is enabled
            if not current_app.config.get("AI_MODULE_ENABLED", False):
                if request.is_json or request.accept_mimetypes.accept_json:
                    return jsonify({
                        "enabled": False,
                        "error": "AI module is disabled",
                        "message": "The SAS AI module is currently disabled.",
                    }), 403
                abort(404)
            
            # HARD CHECK: Feature must be enabled at runtime
            if not check_feature_enabled(feature_key):
                # Log disabled access attempt
                current_app.logger.warning(
                    f"Disabled AI feature '{feature_key}' accessed by user {current_user.email if current_user.is_authenticated else 'anonymous'}"
                )
                
                if request.is_json or request.accept_mimetypes.accept_json:
                    return jsonify({
                        "enabled": False,
                        "error": "Feature is disabled",
                        "message": f"The '{feature_key}' AI feature is currently disabled.",
                    }), 403
                
                # For HTML requests, render branded disabled page
                feature = get_feature_by_key(feature_key)
                return render_template(
                    "ai/feature_disabled.html",
                    feature=feature or {"name": feature_key, "key": feature_key},
                    feature_key=feature_key,
                ), 403
            
            # Feature is enabled, proceed
            return f(*args, **kwargs)
        
        return decorated_function
    return decorator


# Alias for backward compatibility
ai_feature_required = require_ai_feature


def check_ai_module_enabled():
    """
    Check if the AI module is enabled.
    
    Returns:
        bool: True if enabled, False otherwise
    """
    from sas_management.ai.state import is_module_enabled
    return is_module_enabled()


def require_ai_module(f):
    """
    Decorator to require AI module to be enabled.
    
    Usage:
        @require_ai_module
        def my_route():
            ...
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not check_ai_module_enabled():
            if request.is_json or request.accept_mimetypes.accept_json:
                return jsonify({
                    "enabled": False,
                    "error": "AI module is disabled",
                }), 200
            abort(404)
        return f(*args, **kwargs)
    
    return decorated_function

