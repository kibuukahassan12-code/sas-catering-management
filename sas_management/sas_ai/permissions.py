"""SAS AI Permissions - Check if SAS AI is enabled."""

def is_sas_ai_enabled(app):
    """
    Check if SAS AI is enabled in the application config.
    
    Args:
        app: Flask application instance
        
    Returns:
        bool: True if SAS AI is enabled, False otherwise
    """
    return app.config.get("SAS_AI_ENABLED", True)


def require_sas_ai_enabled(f):
    """Decorator to require SAS AI to be enabled."""
    from functools import wraps
    from flask import jsonify, current_app
    
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not is_sas_ai_enabled(current_app):
            return jsonify({
                "success": False,
                "message": "SAS AI is currently offline. Please try again later.",
                "enabled": False
            }), 503
        
        return f(*args, **kwargs)
    
    return decorated_function

