import os

from flask import Flask
from flask_login import LoginManager
from flask_migrate import Migrate
from sqlalchemy.sql import false
from dotenv import load_dotenv
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

load_dotenv()

from config import ProductionConfig
from models import User, db, seed_initial_data
from routes import core_bp
from sentry_setup import init_sentry
from blueprints.catering import catering_bp
# from blueprints.hire import hire_bp
from hire import hire
from blueprints.bakery import bakery_bp
from blueprints.cashbook import cashbook_bp
from blueprints.quotes import quotes_bp
from blueprints.university import university_bp
from blueprints.chat import chat_bp
from blueprints.leads import leads_bp
from blueprints.inventory import inventory_bp
from blueprints.invoices import invoices_bp
from blueprints.payroll import payroll_bp
from blueprints.reports import reports_bp
from blueprints.tasks import tasks_bp
from blueprints.audit import audit_bp
from blueprints.crm import crm_bp
from blueprints.events import events_bp
from blueprints.production import production_bp
from blueprints.pos import pos_bp
from blueprints.accounting import accounting_bp
from blueprints.hr import hr_bp

login_manager = LoginManager()
login_manager.login_view = "core.login"
login_manager.login_message_category = "info"
login_manager.session_protection = "strong"


def create_app():
    from datetime import date
    import logging
    from logging.handlers import RotatingFileHandler
    import sys
    
    # FIX FLASK PATHS (CRITICAL EXE FIX)
    if getattr(sys, 'frozen', False):
        base_path = sys._MEIPASS
        instance_path = os.path.join(base_path, "instance")
        templates_path = os.path.join(base_path, "templates")
        static_path = os.path.join(base_path, "static")
    else:
        base_path = os.path.abspath(os.path.dirname(__file__))
        instance_path = os.path.join(base_path, "instance")
        templates_path = os.path.join(base_path, "templates")
        static_path = os.path.join(base_path, "static")
    
    app = Flask(
        __name__,
        instance_path=instance_path,
        template_folder=templates_path,
        static_folder=static_path
    )
    
    # ENSURE INSTANCE FOLDER EXISTS
    os.makedirs(app.instance_path, exist_ok=True)
    
    # init_sentry(app)
    app.config.from_object(ProductionConfig)
    
    # Enable debug mode for development (shows full error tracebacks)
    app.config['DEBUG'] = True
    app.config['ENV'] = 'development'
    
    # FIX DATABASE PATH
    db_path = os.path.join(app.instance_path, "sas.db")
    app.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{db_path}"

    # Setup error logging
    # ---------------- SAFE LOGS FOLDER CREATION ----------------
    base_dir = os.path.dirname(os.path.abspath(__file__))
    logs_path = os.path.join(base_dir, "logs")
    try:
        os.makedirs(logs_path, exist_ok=True)
    except Exception as e:
        print("Error creating logs folder:", e)
    # ------------------------------------------------------------
    
    handler = RotatingFileHandler(
        os.path.join(logs_path, "error.log"),
        maxBytes=500000,
        backupCount=5,
        delay=True
    )
    handler.setLevel(logging.WARNING)
    app.logger.addHandler(handler)

    db.init_app(app)
    login_manager.init_app(app)
    
    # Initialize Flask-Limiter for rate limiting
    limiter = Limiter(
        get_remote_address,
        app=app,
        default_limits=["200 per hour", "20 per minute"]
    )
    # Make limiter available globally
    app.limiter = limiter
    
    # Initialize Flask-Migrate for database migrations
    # Note: db.create_all() is kept for initial dev safety, but migrations are preferred
    migrate = Migrate(app, db)
    
    # Global Safe-Mode Fix: Bypass RBAC for unassigned users
    @app.before_request
    def bypass_rbac_for_unassigned_users():
        from flask_login import current_user
        if not current_user.is_authenticated:
            return
        if getattr(current_user, "role_id", None) is None:
            return  # allow user to continue normally

    app.register_blueprint(core_bp)
    app.register_blueprint(catering_bp)
    app.register_blueprint(hire, url_prefix="/hire")
    # app.register_blueprint(hire_bp)
    
    # Register Equipment Maintenance blueprint
    try:
        from blueprints.hire.maintenance_routes import maintenance_bp
        app.register_blueprint(maintenance_bp)
    except Exception as e:
        print(f"⚠️  Equipment Maintenance module disabled: {e}")
        if app.config.get("ENV") != "production":
            import traceback
            traceback.print_exc()
    app.register_blueprint(bakery_bp)
    app.register_blueprint(cashbook_bp)
    app.register_blueprint(quotes_bp)
    app.register_blueprint(university_bp)
    app.register_blueprint(chat_bp)
    app.register_blueprint(leads_bp)
    app.register_blueprint(inventory_bp)
    app.register_blueprint(invoices_bp)
    app.register_blueprint(payroll_bp)
    app.register_blueprint(reports_bp)
    app.register_blueprint(tasks_bp)
    app.register_blueprint(audit_bp)
    app.register_blueprint(crm_bp)
    app.register_blueprint(events_bp)
    app.register_blueprint(production_bp)
    app.register_blueprint(pos_bp)
    app.register_blueprint(accounting_bp)
    
    # Register Floor Planner blueprint
    from blueprints.floorplanner import floorplanner_bp
    app.register_blueprint(floorplanner_bp)
    
    # Register Floor Plans Builder blueprint
    from blueprints.floor_plans import floor_plans_bp
    app.register_blueprint(floor_plans_bp, url_prefix="/")
    
    # Register HR blueprint
    from blueprints.hr import hr_bp
    app.register_blueprint(hr_bp)
    
    # Register Production Recipes blueprint
    from blueprints.production_recipes import recipes_bp
    app.register_blueprint(recipes_bp)
    
    # Register Search blueprint
    from blueprints.search import search_bp
    app.register_blueprint(search_bp)
    
    # Register Analytics blueprint
    try:
        from blueprints.analytics import analytics_bp
        app.register_blueprint(analytics_bp)
    except Exception as e:
        print(f"⚠️  Analytics module disabled: {e}")
        if app.config.get("ENV") != "production":
            import traceback
            traceback.print_exc()
    
    # Register Admin blueprint
    from blueprints.admin import admin_bp
    app.register_blueprint(admin_bp)
    
    # Register Admin Users blueprint
    from blueprints.admin.admin_users_assign import admin_users
    app.register_blueprint(admin_users, url_prefix="/admin")
    
    # Register RBAC blueprint
    from blueprints.admin.rbac import rbac_bp
    app.register_blueprint(rbac_bp, url_prefix="/admin/rbac")
    
    # Register Auth blueprint
    from blueprints.auth import auth_bp
    app.register_blueprint(auth_bp)
    
    # Activity logging middleware
    @app.before_request
    def log_user_actions():
        from flask import request
        from flask_login import current_user
        from models import ActivityLog
        if current_user.is_authenticated:
            try:
                entry = ActivityLog(
                    user_id=current_user.id,
                    action=request.endpoint,
                    ip_address=request.remote_addr,
                    url=request.url
                )
                db.session.add(entry)
                db.session.commit()
            except Exception as e:
                # Don't break the app if logging fails
                db.session.rollback()
                if app.config.get("ENV") != "production":
                    print(f"⚠️  Activity logging error: {e}")
    
    # Add template context processor for permissions
    @app.context_processor
    def inject_permissions():
        from utils.permissions import has_permission
        return dict(has_permission=has_permission)
    
    # Global error handler to show full traceback in browser
    import traceback
    from flask import Response
    from werkzeug.exceptions import HTTPException
    
    @app.errorhandler(Exception)
    def handle_exception(e):
        # Pass through HTTP exceptions (like 404) to Flask's default handlers
        if isinstance(e, HTTPException):
            return e
        
        tb = traceback.format_exc()
        print("\n====== FULL ERROR TRACEBACK ======\n")
        print(tb)
        print("==================================\n")
        
        # Log to file as well
        try:
            app.logger.error("Unhandled exception:\n" + tb)
        except:
            pass  # Don't fail if logging fails
        
        # Return traceback to browser so we can see the REAL cause
        return Response(f"<pre style='background:#1e1e1e;color:#d4d4d4;padding:20px;font-family:monospace;white-space:pre-wrap;'>{tb}</pre>", mimetype="text/html"), 500
    
    # Specific 500 error handler
    @app.errorhandler(500)
    def handle_500(e):
        import traceback
        tb = traceback.format_exc()
        return f"<pre>{tb}</pre>", 500
    
    # Register BI blueprint
    from blueprints.bi import bi_bp
    app.register_blueprint(bi_bp)
    
    # Register Profitability blueprint
    from blueprints.profitability import profitability_bp
    app.register_blueprint(profitability_bp)
    
    # Register Communication blueprint
    from blueprints.communication import comm_bp
    app.register_blueprint(comm_bp)
    
    # Register Premium Module blueprints
    from blueprints.menu_builder import menu_builder_bp
    from blueprints.contracts import contracts_bp
    app.register_blueprint(menu_builder_bp)
    app.register_blueprint(contracts_bp)
    
    # Register Integrations blueprint (with safe fallback)
    try:
        from blueprints.integrations import integrations_bp
        app.register_blueprint(integrations_bp)
    except Exception as e:
        print(f"⚠️  Integrations module disabled: {e}")
        if app.config.get("ENV") != "production":
            import traceback
            traceback.print_exc()
    
    # Register AI Suite blueprint (with safe fallback)
    try:
        from blueprints.ai import ai_bp
        app.register_blueprint(ai_bp)
    except Exception as e:
        print(f"⚠️  AI Suite module disabled: {e}")
        if app.config.get("ENV") != "production":
            import traceback
            traceback.print_exc()
    
    # Register Enterprise Module blueprints (with safe fallbacks)
    try:
        from blueprints.client_portal import client_portal_bp
        app.register_blueprint(client_portal_bp)
    except Exception as e:
        print(f"⚠️  Client Portal module disabled: {e}")
    
    try:
        from blueprints.proposals import proposals_bp
        app.register_blueprint(proposals_bp)
    except Exception as e:
        print(f"⚠️  Proposals module disabled: {e}")
    
    try:
        from blueprints.dispatch import dispatch_bp
        app.register_blueprint(dispatch_bp)
    except Exception as e:
        print(f"⚠️  Dispatch module disabled: {e}")
    
    try:
        from blueprints.kds import kds_bp
        app.register_blueprint(kds_bp)
    except Exception as e:
        print(f"⚠️  KDS module disabled: {e}")
    
    try:
        from blueprints.mobile_staff import mobile_staff_bp
        app.register_blueprint(mobile_staff_bp)
    except Exception as e:
        print(f"⚠️  Mobile Staff module disabled: {e}")
    
    try:
        from blueprints.timeline import timeline_bp
        app.register_blueprint(timeline_bp)
    except Exception as e:
        print(f"⚠️  Timeline module disabled: {e}")
    
    try:
        from blueprints.incidents import incidents_bp
        app.register_blueprint(incidents_bp)
    except Exception as e:
        print(f"⚠️  Incidents module disabled: {e}")
    
    try:
        from blueprints.automation import automation_bp
        app.register_blueprint(automation_bp)
    except Exception as e:
        print(f"⚠️  Automation module disabled: {e}")
    
    try:
        from blueprints.vendors import vendors_bp
        app.register_blueprint(vendors_bp)
    except Exception as e:
        print(f"⚠️  Vendors module disabled: {e}")
    
    try:
        from blueprints.food_safety import food_safety_bp
        app.register_blueprint(food_safety_bp)
    except Exception as e:
        print(f"⚠️  Food Safety module disabled: {e}")
    
    # Register Branches blueprint (if multi-branch enabled)
    if app.config.get("ENABLE_BRANCHES", False):
        try:
            from blueprints.branches import branches_bp
            app.register_blueprint(branches_bp)
        except Exception as e:
            print(f"⚠️  Branches module disabled: {e}")

    with app.app_context():
        # Ensure AI directories exist
        ai_assets_dir = os.path.join(app.instance_path, "ai_assets")
        ai_models_dir = os.path.join(app.instance_path, "ai_models")
        os.makedirs(ai_assets_dir, exist_ok=True)
        os.makedirs(ai_models_dir, exist_ok=True)
        
        # Check if database exists and handle schema mismatches
        db_path = os.path.join(app.instance_path, "sas.db")
        # Also check for legacy database names
        db_path_alt = os.path.join(app.instance_path, "app.db")
        db_path_alt2 = os.path.join(app.instance_path, "site.db")
        
        # Try to detect if we need to recreate database (DEV mode only)
        if app.config.get("ENV") != "production":
            # In development, check if bakery_item table exists and has correct columns
            try:
                from sqlalchemy import inspect, text
                inspector = inspect(db.engine)
                if "bakery_item" in inspector.get_table_names():
                    # Check if required columns exist
                    columns = [col['name'] for col in inspector.get_columns("bakery_item")]
                    required_cols = ["selling_price", "cost_price", "preparation_time", "created_at"]
                    missing_cols = [col for col in required_cols if col not in columns]
                    
                    if missing_cols:
                        print(f"⚠️  Bakery table missing columns: {missing_cols}")
                        print("   Running migration script...")
                        # Try to run migration
                        try:
                            from migrate_bakery_module import migrate_bakery
                            migrate_bakery()
                        except Exception as mig_error:
                            print(f"   Migration failed: {mig_error}")
                            print("   Attempting to add columns directly...")
                            for col in missing_cols:
                                try:
                                    if col == "selling_price":
                                        db.session.execute(text("ALTER TABLE bakery_item ADD COLUMN selling_price NUMERIC(14,2) DEFAULT 0.00"))
                                    elif col == "cost_price":
                                        db.session.execute(text("ALTER TABLE bakery_item ADD COLUMN cost_price NUMERIC(14,2) DEFAULT 0.00"))
                                    elif col == "preparation_time":
                                        db.session.execute(text("ALTER TABLE bakery_item ADD COLUMN preparation_time INTEGER"))
                                    elif col == "created_at":
                                        db.session.execute(text("ALTER TABLE bakery_item ADD COLUMN created_at DATETIME"))
                                    db.session.commit()
                                    print(f"   ✓ Added column: {col}")
                                except Exception as e:
                                    if "duplicate column" not in str(e).lower():
                                        print(f"   ✗ Error adding {col}: {e}")
                                    db.session.rollback()
            except Exception as e:
                print(f"⚠️  Could not check database schema: {e}")
        
        # Create all tables
        db.create_all()
        
        # Seed initial data
        seed_initial_data(db)
        
        # Configure relationship ordering (must be after all models are defined and mapped)
        # This ensures all relationships are properly configured
        try:
            from models import configure_relationship_ordering
            configure_relationship_ordering()
        except Exception as e:
            # Log but don't fail - relationships should work without this
            if app.config.get("ENV") != "production":
                print(f"⚠️  Relationship ordering configuration warning: {e}")
        
        # Set up audit logging
        from models import setup_audit_logging
        setup_audit_logging()
        
        # Ensure upload directory exists
        upload_folder = os.path.join(app.instance_path, "..", app.config.get("UPLOAD_FOLDER", "files"))
        upload_folder = os.path.abspath(upload_folder)
        os.makedirs(upload_folder, exist_ok=True)
        
        # Ensure receipts directory exists
        receipts_folder = os.path.join(app.instance_path, "receipts")
        os.makedirs(receipts_folder, exist_ok=True)
        
        # Ensure bakery uploads directory exists
        bakery_uploads_folder = os.path.join(app.instance_path, "bakery_uploads")
        os.makedirs(bakery_uploads_folder, exist_ok=True)
        
        # Ensure university uploads directory exists
        university_uploads_folder = os.path.join(app.instance_path, "university_uploads")
        os.makedirs(university_uploads_folder, exist_ok=True)
        os.makedirs(os.path.join(university_uploads_folder, "documents"), exist_ok=True)
        os.makedirs(os.path.join(university_uploads_folder, "images"), exist_ok=True)
        os.makedirs(os.path.join(university_uploads_folder, "videos"), exist_ok=True)
        os.makedirs(os.path.join(university_uploads_folder, "certificates"), exist_ok=True)
        
        # Ensure HR uploads directory exists
        hr_uploads_folder = os.path.join(app.instance_path, "hr_uploads")
        os.makedirs(hr_uploads_folder, exist_ok=True)
        os.makedirs(os.path.join(hr_uploads_folder, "employee_photos"), exist_ok=True)
        os.makedirs(os.path.join(hr_uploads_folder, "docs"), exist_ok=True)
        
        # Ensure Production uploads directory exists
        production_uploads_folder = os.path.join(app.instance_path, "production_uploads")
        os.makedirs(production_uploads_folder, exist_ok=True)
        os.makedirs(os.path.join(production_uploads_folder, "recipe_images"), exist_ok=True)
        os.makedirs(os.path.join(production_uploads_folder, "waste_logs"), exist_ok=True)
        
        # Ensure BI uploads directory exists
        bi_uploads_folder = os.path.join(app.instance_path, "bi_uploads")
        os.makedirs(bi_uploads_folder, exist_ok=True)
        os.makedirs(os.path.join(bi_uploads_folder, "sample_images"), exist_ok=True)
        
        # Ensure Communication uploads directory exists
        comm_uploads_folder = os.path.join(app.instance_path, "comm_uploads")
        os.makedirs(comm_uploads_folder, exist_ok=True)
        os.makedirs(os.path.join(comm_uploads_folder, "attachments"), exist_ok=True)
        
        # Ensure Premium Assets directory exists
        premium_assets_folder = os.path.join(app.instance_path, "premium_assets")
        os.makedirs(premium_assets_folder, exist_ok=True)
        os.makedirs(os.path.join(premium_assets_folder, "menu_images"), exist_ok=True)
        os.makedirs(os.path.join(premium_assets_folder, "contracts"), exist_ok=True)
        
        # Create integrations assets directory
        integrations_assets_folder = os.path.join(app.instance_path, "integrations_assets")
        os.makedirs(integrations_assets_folder, exist_ok=True)

    @app.context_processor
    def inject_globals():
        return {
            "CURRENCY": app.config.get("CURRENCY_PREFIX", "UGX "),
            "date": date
        }

    # Load system tester if available (for health checks)
    try:
        from tools.system_tester import run_full_test
        # Test can be run manually via: python tools/system_tester.py
    except ImportError:
        pass  # System tester is optional
    
    return app


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


app = create_app()

# Export limiter for use in routes
limiter = app.limiter if hasattr(app, 'limiter') else None

# Apply rate limiting to login route
if limiter:
    # Get the login view function and wrap it with rate limiting
    from flask import current_app
    view_func = app.view_functions.get('core.login')
    if view_func:
        app.view_functions['core.login'] = limiter.limit("5 per minute")(view_func)


if __name__ == "__main__":
    import webbrowser
    import threading
    import time
    import sys
    import os
    
    # Add parent directory to path for updater import
    parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    if parent_dir not in sys.path:
        sys.path.insert(0, parent_dir)
    
    app = create_app()
    
    # Check for updates in background (non-blocking)
    try:
        import updater
        updater.check_for_updates_background()
    except Exception as e:
        print(f"Update check initialization failed: {e}")
        # Continue running app even if updater fails
    
    # Open browser after a short delay
    def open_browser():
        time.sleep(1.5)
        webbrowser.open('http://127.0.0.1:5000')
    
    browser_thread = threading.Thread(target=open_browser)
    browser_thread.daemon = True
    browser_thread.start()
    
    app.run(
        host="127.0.0.1",
        port=5000,
        debug=False
    )

