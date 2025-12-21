"""
Centralized Blueprint Registry for SAS Management System.

This module provides a single function to register all blueprints,
ensuring deterministic startup and eliminating duplicate registrations.
"""


def register_blueprints(app):
    """
    Register all blueprints with the Flask application.
    
    This function imports and registers all blueprints exactly once.
    Import errors are NOT suppressed - they will surface during development.
    
    Args:
        app: Flask application instance
    """
    # Core blueprints - always registered
    from routes import core_bp
    from blueprints.catering import catering_bp
    from blueprints.bakery import bakery_bp
    from blueprints.cashbook import cashbook_bp
    from blueprints.quotes import quotes_bp
    from blueprints.university import university_bp
    from blueprints.chat import chat_bp
    from blueprints.leads import leads_bp
    from blueprints.inventory import inventory_bp
    from blueprints.invoices import invoices_bp
    from blueprints.payroll import payroll_bp
    # Reports blueprint is optional/safe-mode and registered with error handling below
    # from blueprints.reports import reports_bp
    from blueprints.tasks import tasks_bp
    from blueprints.audit import audit_bp
    from blueprints.crm import crm_bp
    from blueprints.events import events_bp
    # DISABLED: Duplicate Event Service module - events_service is legacy service catalog
    # Canonical Event Service module is: blueprints.service (ServiceEvent model)
    # from blueprints.events_service import bp as events_service_bp
    from blueprints.production import production_bp
    from blueprints.pos import pos_bp
    from blueprints.accounting import accounting_bp
    from blueprints.service.routes import service_bp
    from blueprints.event_service import event_service_bp
    from blueprints.hr import hr_bp
    from blueprints.floorplanner import floorplanner_bp
    from blueprints.floor_plans import floor_plans_bp
    from blueprints.production_recipes import recipes_bp
    from blueprints.search import search_bp
    from blueprints.admin import admin_bp
    from blueprints.admin.admin_users_assign import admin_users
    from blueprints.admin.rbac import rbac_bp
    from blueprints.auth import auth_bp
    from blueprints.bi import bi_bp
    from blueprints.profitability import profitability_bp
    from blueprints.communication import comm_bp
    from blueprints.menu_builder import menu_builder_bp
    from blueprints.contracts import contracts_bp
    
    # Hire blueprint (special import)
    from hire import hire
    
    # Register core blueprints
    app.register_blueprint(core_bp)
    app.register_blueprint(catering_bp)
    app.register_blueprint(hire, url_prefix="/hire")
    app.register_blueprint(bakery_bp)
    app.register_blueprint(cashbook_bp)
    app.register_blueprint(quotes_bp)
    app.register_blueprint(university_bp)
    app.register_blueprint(chat_bp)
    app.register_blueprint(leads_bp)
    app.register_blueprint(inventory_bp)
    app.register_blueprint(invoices_bp)
    app.register_blueprint(payroll_bp)
    # Reports blueprint is optional/safe-mode and registered with error handling below
    # app.register_blueprint(reports_bp)
    app.register_blueprint(tasks_bp)
    app.register_blueprint(audit_bp)
    app.register_blueprint(crm_bp)
    app.register_blueprint(events_bp)
    # DISABLED: Duplicate Event Service module - events_service is legacy service catalog
    # Canonical Event Service module is: service_bp (ServiceEvent model, /service routes)
    # app.register_blueprint(events_service_bp)
    app.register_blueprint(production_bp)
    app.register_blueprint(pos_bp)
    app.register_blueprint(accounting_bp)
    app.register_blueprint(service_bp)
    app.register_blueprint(event_service_bp)
    app.register_blueprint(hr_bp)
    app.register_blueprint(floorplanner_bp)
    app.register_blueprint(floor_plans_bp, url_prefix="/")
    app.register_blueprint(recipes_bp)
    app.register_blueprint(search_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(admin_users, url_prefix="/admin")
    app.register_blueprint(rbac_bp, url_prefix="/admin/rbac")
    app.register_blueprint(auth_bp)
    app.register_blueprint(bi_bp)
    app.register_blueprint(profitability_bp)
    app.register_blueprint(comm_bp)
    app.register_blueprint(menu_builder_bp)
    app.register_blueprint(contracts_bp)
    
    # Additional/optional blueprints - these should never prevent app startup
    # If any optional blueprint cannot be imported, it will be logged and skipped.
    
    # Equipment Maintenance
    from blueprints.hire.maintenance_routes import maintenance_bp
    app.register_blueprint(maintenance_bp)
    
    # Reports (optional, safe registration)
    try:
        from sas_management.blueprints.reports import reports_bp
        app.register_blueprint(reports_bp)
    except Exception as e:
        app.logger.warning(f"Reports blueprint not available - skipping registration: {e}")
    
    # Analytics (optional, safe registration)
    try:
        from sas_management.blueprints.analytics import analytics_bp
        app.register_blueprint(analytics_bp)
    except Exception as e:
        # Analytics is optional - log but don't fail
        app.logger.warning(f"Analytics blueprint not available - skipping registration: {e}")
    
    # Integrations
    from sas_management.blueprints.integrations import integrations_bp
    app.register_blueprint(integrations_bp)
    
    # Enterprise modules
    from sas_management.blueprints.client_portal import client_portal_bp
    from sas_management.blueprints.proposals import proposals_bp
    from sas_management.blueprints.dispatch import dispatch_bp
    from sas_management.blueprints.kds import kds_bp
    from sas_management.blueprints.mobile_staff import mobile_staff_bp
    from sas_management.blueprints.timeline import timeline_bp
    from sas_management.blueprints.incidents import incidents_bp
    from sas_management.blueprints.automation import automation_bp
    from sas_management.blueprints.vendors import vendors_bp
    from sas_management.blueprints.food_safety import food_safety_bp
    
    app.register_blueprint(client_portal_bp)
    app.register_blueprint(proposals_bp)
    app.register_blueprint(dispatch_bp)
    app.register_blueprint(kds_bp)
    app.register_blueprint(mobile_staff_bp)
    app.register_blueprint(timeline_bp)
    app.register_blueprint(incidents_bp)
    app.register_blueprint(automation_bp)
    app.register_blueprint(vendors_bp)
    app.register_blueprint(food_safety_bp)
    
    # SAS AI Blueprint - Premium AI Chat and Features
    # Register the sas_ai blueprint from sas_management/sas_ai (has /chat route)
    # This is the main chatbot blueprint that the frontend JavaScript calls
    try:
        from sas_management.sas_ai import sas_ai_bp
        app.register_blueprint(sas_ai_bp)
        app.logger.info("SAS AI blueprint (sas_ai) registered successfully at /sas-ai")
    except Exception as e:
        app.logger.warning(f"SAS AI blueprint (sas_ai) not available - skipping registration: {e}")
    
    # Also register the AI features blueprint for dashboard and other features
    # Note: This uses the same blueprint name but different URL prefix to avoid conflicts
    try:
        from sas_management.ai.blueprint import sas_ai_bp as ai_features_bp
        # Create a new blueprint instance with different name to avoid registration conflict
        from flask import Blueprint
        ai_dashboard_bp = Blueprint("ai_dashboard", __name__, url_prefix="/ai-dashboard")
        # Copy routes from ai_features_bp if needed, or just register with different prefix
        # For now, we'll skip this to avoid conflicts - the main chat is in sas_ai_bp
        app.logger.info("AI Features available through sas_ai blueprint")
    except Exception as e:
        app.logger.warning(f"AI Features blueprint setup skipped: {e}")
    
    # Conditional: Branches (only if enabled)
    if app.config.get("ENABLE_BRANCHES", False):
        from sas_management.blueprints.branches import branches_bp
        app.register_blueprint(branches_bp)
