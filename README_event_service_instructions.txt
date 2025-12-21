Blueprint registration (if not already registered)
-------------------------------------------------
Open sas_management/app.py (or wherever you register blueprints) and ensure:

from sas_management.blueprints.service import service_bp

try:
    if 'service' not in app.blueprints:
        app.register_blueprint(service_bp)
except Exception as e:
    app.logger.error("Failed to register service blueprint: %s", e)

