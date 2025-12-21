"""SAS AI Blueprint Registration - Safe registration helper."""
from flask import Flask


def register_sas_ai_blueprint(app: Flask):
    """
    Safely register the SAS AI blueprint.
    
    Args:
        app: Flask application instance
    """
    try:
        from . import sas_ai_bp
        
        # Set default config if not set
        if "SAS_AI_ENABLED" not in app.config:
            app.config["SAS_AI_ENABLED"] = True
        
        app.register_blueprint(sas_ai_bp)
        app.logger.info("SAS AI blueprint registered successfully")
        return True
        
    except ImportError as e:
        app.logger.warning(f"Could not import SAS AI blueprint: {e}")
        return False
    except Exception as e:
        app.logger.error(f"Error registering SAS AI blueprint: {e}")
        return False

