print('RUNNING APP.PY FROM:', __file__)
import os
import sys

# Load environment variables FIRST before any other imports
# This ensures OPENAI_API_KEY and other env vars are available immediately
from dotenv import load_dotenv
load_dotenv()

# Prevent import of build/ modules
build_path = os.path.join(os.path.dirname(__file__), 'build')
if build_path in sys.path:
    sys.path.remove(build_path)

# Add current directory to Python path for relative imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from flask import Flask
from flask_login import LoginManager
from flask_migrate import Migrate
from sqlalchemy.sql import false
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

from config import ProductionConfig
from sas_management.models import User, db, seed_initial_data

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
    
    # Create university upload directory
    upload_path = os.path.join(app.root_path, "static", "uploads", "university")
    os.makedirs(upload_path, exist_ok=True)
    
    # Set university upload config
    app.config["UNIVERSITY_UPLOAD_FOLDER"] = app.config.get("UNIVERSITY_UPLOAD_FOLDER", "sas_management/static/uploads/university")
    app.config["UNIVERSITY_MAX_CONTENT_LENGTH"] = app.config.get("UNIVERSITY_MAX_CONTENT_LENGTH", 1024 * 1024 * 1024)  # 1GB
    
    # init_sentry(app)
    app.config.from_object(ProductionConfig)
    
    # Load debug mode from environment or config (default: False for production)
    app.config['DEBUG'] = os.getenv('FLASK_DEBUG', 'False').lower() == 'true' or app.config.get('DEBUG', False)
    app.config['ENV'] = os.getenv('FLASK_ENV', app.config.get('ENV', 'production'))
    
    # Ensure AI module is enabled by default (can be overridden by config)
    if 'AI_MODULE_ENABLED' not in app.config:
        app.config['AI_MODULE_ENABLED'] = True
    
    # Initialize AI features state from config defaults
    if 'AI_FEATURES' in app.config and isinstance(app.config['AI_FEATURES'], dict):
        # Features are already set from config.py
        pass
    else:
        # Set default AI features to enabled
        app.config['AI_FEATURES'] = app.config.get('AI_FEATURES', {})
    
    # Use DATABASE_URL from environment - Supabase PostgreSQL
    db_url = os.environ.get('DATABASE_URL', '')
    if not db_url:
        # Fallback to SQLite if no DATABASE_URL set
        db_path = os.path.join(app.instance_path, "sas.db")
        db_url = f"sqlite:///{db_path}"
    app.config["SQLALCHEMY_DATABASE_URI"] = db_url

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
        delay=True,
        encoding='utf-8'
    )
    handler.setLevel(logging.WARNING)
    app.logger.addHandler(handler)
    
    # Reduce development log noise: Set Werkzeug logger to WARNING level only
    werkzeug_logger = logging.getLogger('werkzeug')
    werkzeug_logger.setLevel(logging.WARNING)

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
        # Safe guard: prevent crashes when login manager is not yet initialized
        if not hasattr(current_user, "is_authenticated") or not current_user.is_authenticated:
            return
        if getattr(current_user, "role_id", None) is None:
            return  # allow user to continue normally
    
    # First login password change requirement - block all routes except change-password
    @app.before_request
    def enforce_first_login_password_change():
        from flask import request, redirect, url_for
        from flask_login import current_user
        
        # Only check authenticated users
        if not hasattr(current_user, "is_authenticated") or not current_user.is_authenticated:
            return
        
        # Admin is exempt from first login password change requirement
        is_admin = hasattr(current_user, 'is_admin') and current_user.is_admin
        if is_admin:
            return
        
        # Check if user needs to change password on first login
        first_login = getattr(current_user, 'first_login', True)
        must_change = getattr(current_user, 'must_change_password', False) or getattr(current_user, 'force_password_change', False)
        
        if first_login or must_change:
            # Allow access to change password routes, logout, and static files
            allowed_routes = [
                'core.force_change_password',
                'core.change_password',
                'auth.change_password',
                'auth.set_new_password',
                'core.logout',
                'static',  # Allow static files (CSS, JS, images)
                None  # Allow routes with no endpoint (some error handlers)
            ]
            
            # Check if current route is in allowed list
            endpoint = request.endpoint
            if endpoint and endpoint not in allowed_routes:
                # Prevent infinite redirects - only redirect if not already going to change password
                if request.path not in ['/force-change-password', '/change-password', '/auth/change-password', '/auth/set-new-password']:
                    return redirect(url_for("core.force_change_password"))

    # Register all blueprints using centralized registry
    # This ensures deterministic startup and eliminates duplicate registrations
    from sas_management.blueprints import register_blueprints
    register_blueprints(app)
    
    # Register AI blueprint safely (must not crash system if AI fails)
    try:
        from sas_management.blueprints.ai.routes import ai_bp
        # Check if "ai" blueprint is already registered to prevent duplicate registration
        if "ai" not in app.blueprints:
            app.register_blueprint(ai_bp)
            app.logger.info("AI blueprint registered successfully")
        else:
            app.logger.info("AI blueprint already registered, skipping duplicate registration")
    except Exception as e:
        app.logger.warning(f"AI blueprint registration failed (non-fatal): {e}")
        # System continues without AI - this is acceptable
    
    # Apply rate limiting to login route after blueprints are registered
    if hasattr(app, 'limiter') and app.limiter:
        view_func = app.view_functions.get('core.login')
        if view_func:
            app.view_functions['core.login'] = app.limiter.limit("5 per minute")(view_func)
    
    # Lightweight expired roles check (runs occasionally, not every request)
    _last_expired_check = {"time": 0}
    @app.before_request
    def check_expired_roles_lightweight():
        """Lightweight check for expired roles - runs max once per minute."""
        import time
        current_time = time.time()
        # Only check every 60 seconds to avoid blocking requests
        if current_time - _last_expired_check["time"] > 60:
            try:
                from sas_management.utils.role_utils import check_expired_roles
                check_expired_roles()
                _last_expired_check["time"] = current_time
            except Exception as e:
                # Don't break requests if check fails
                if app.config.get("DEBUG", False):
                    app.logger.debug(f"Expired roles check error (non-fatal): {e}")
    
    # Activity logging middleware - safe error handling that doesn't break requests
    @app.before_request
    def log_user_actions():
        from flask import request
        from flask_login import current_user
        from sas_management.models import ActivityLog
        if current_user.is_authenticated:
            try:
                entry = ActivityLog(
                    user_id=current_user.id,
                    action=request.endpoint,
                    ip_address=request.remote_addr,
                    url=request.url
                )
                db.session.add(entry)
                # Use flush instead of commit to avoid blocking on every request
                # Actual commit happens at end of request via after_request
                db.session.flush()
            except Exception as e:
                # Don't break the app if logging fails - rollback and continue
                db.session.rollback()
                # Only log in development to avoid log noise in production
                if app.config.get("DEBUG", False):
                    app.logger.debug(f"Activity logging error (non-fatal): {e}")
    
    # Commit activity logs at end of request (batched)
    @app.after_request
    def commit_activity_logs(response):
        try:
            # Only commit if there are pending changes (from activity logging)
            if db.session.dirty or db.session.new:
                db.session.commit()
        except Exception as e:
            # Rollback on error but don't break the response
            db.session.rollback()
            if app.config.get("DEBUG", False):
                app.logger.debug(f"Activity log commit error (non-fatal): {e}")
        return response
    
    # Context processor to inject modules into all templates for authenticated users
    @app.context_processor
    def inject_modules():
        from flask_login import current_user
        from flask import url_for
        from sas_management.utils.permissions import has_permission
        
        def has_any_permission(*permission_codes):
            """Check if user has any of the given permissions."""
            for perm in permission_codes:
                if has_permission(perm):
                    return True
            return False
        
        def format_millions(value):
            """Format number with M suffix for millions."""
            if value is None:
                return "0"
            try:
                val = float(value)
                if val >= 1_000_000:
                    return f"{val/1_000_000:.0f}M"
                elif val >= 1_000:
                    return f"{val/1_000:.0f}K"
                else:
                    return f"{val:,.0f}"
            except:
                return str(value)
        
        modules = []
        
        # Only compute modules for authenticated users
        if current_user.is_authenticated:
            # Check if user is admin (has full access)
            is_admin = False
            if hasattr(current_user, 'role_obj') and current_user.role_obj:
                if current_user.role_obj.name == 'ADMIN':
                    is_admin = True
            elif hasattr(current_user, 'role') and str(current_user.role) == 'UserRole.Admin':
                is_admin = True
            
            # Admin gets ALL modules
            if is_admin:
                modules.extend([
                    {"name": "Dashboard", "url": url_for("core.dashboard")},
                    {"name": "Clients CRM", "url": url_for("core.clients_list")},
                    {
                        "name": "Events",
                        "url": url_for("events.events_list"),
                        "children": [
                            {"name": "All Events", "url": url_for("events.events_list")},
                            {"name": "Create Event", "url": url_for("events.event_create")},
                            {"name": "Venues", "url": url_for("events.venues_list")},
                            {"name": "Menu Packages", "url": url_for("events.menu_packages_list")},
                            {"name": "Vendors", "url": url_for("events.vendors_manage")},
                            {"name": "Floor Planner", "url": url_for("floorplanner.dashboard")},
                            {"name": "Tasks", "url": url_for("tasks.task_list")},
                        ]
                    },
                    {
                        "name": "Hire Department",
                        "url": url_for("hire.index"),
                        "children": [
                            {"name": "Hire Overview", "url": url_for("hire.index")},
                            {"name": "Hire Inventory", "url": url_for("hire.inventory_list")},
                            {"name": "Hire Orders", "url": url_for("hire.orders_list")},
                            {"name": "Equipment Maintenance", "url": url_for("hire.maintenance_list")},
                        ]
                    },
                    {
                        "name": "Event Service",
                        "url": url_for("service.dashboard"),
                        "children": [
                            {"name": "Services Overview", "url": url_for("service.dashboard")},
                            {"name": "All Events", "url": url_for("service.events")},
                            {"name": "Timeline", "url": url_for("event_service.timeline_index")},
                            {"name": "Documents", "url": url_for("event_service.documents_index")},
                            {"name": "Checklists", "url": url_for("event_service.service_checklists")},
                            {"name": "Messages", "url": url_for("event_service.service_messages")},
                            {"name": "Reports", "url": url_for("event_service.service_reports")},
                            {"name": "Analytics", "url": url_for("event_service.service_analytics")},
                        ]
                    },
                    {
                        "name": "Production Department",
                        "url": url_for("production.index"),
                        "children": [
                            {"name": "Production Overview", "url": url_for("production.index")},
                            {"name": "Menu Builder", "url": url_for("menu_builder.dashboard")},
                            {"name": "Catering Menu", "url": url_for("catering.menu_list")},
                            {"name": "Ingredient Inventory", "url": url_for("inventory.ingredients_list")},
                            {"name": "Kitchen Checklist", "url": url_for("production.kitchen_checklist_list")},
                            {"name": "Delivery QC Checklist", "url": url_for("production.delivery_qc_list")},
                            {"name": "Food Safety Logs", "url": url_for("production.food_safety_list")},
                            {"name": "Hygiene Reports", "url": url_for("production.hygiene_reports_list")},
                        ]
                    },
                    {
                        "name": "Accounting Department",
                        "url": url_for("accounting.dashboard"),
                        "children": [
                            {"name": "Accounting Overview", "url": url_for("accounting.dashboard")},
                            {"name": "Receipting System", "url": url_for("accounting.receipts_list")},
                            {"name": "Quotations", "url": url_for("quotes.list_quotes")},
                            {"name": "Invoices", "url": url_for("invoices.invoice_list")},
                            {"name": "Cashbook", "url": url_for("cashbook.index")},
                            {"name": "Financial Reports", "url": url_for("reports.reports_index")},
                            {"name": "Payroll Management", "url": url_for("payroll.payroll_list")},
                        ]
                    },
                    {
                        "name": "Bakery Department",
                        "url": url_for("bakery.dashboard"),
                        "children": [
                            {"name": "Bakery Overview", "url": url_for("bakery.dashboard")},
                            {"name": "Bakery Menu", "url": url_for("bakery.items_list")},
                            {"name": "Bakery Orders", "url": url_for("bakery.orders_list")},
                            {"name": "Production Sheet", "url": url_for("bakery.production_sheet")},
                            {"name": "Reports", "url": url_for("bakery.reports")},
                        ]
                    },
                    {"name": "POS System", "url": url_for("pos.index")},
                    {
                        "name": "HR Department",
                        "url": url_for("hr.dashboard"),
                        "children": [
                            {"name": "HR Overview", "url": url_for("hr.dashboard")},
                            {"name": "Employee Management", "url": url_for("hr.employee_list")},
                            {"name": "Roster Builder", "url": url_for("hr.roster_builder")},
                            {"name": "Leave Requests", "url": url_for("hr.leave_queue")},
                            {"name": "Attendance Review", "url": url_for("hr.attendance_review")},
                            {"name": "Payroll Export", "url": url_for("hr.payroll_export")},
                        ]
                    },
                    {"name": "CRM Pipeline", "url": url_for("crm.pipeline")},
                    {"name": "Dispatch", "url": url_for("dispatch.dashboard")},
                    {"name": "Employee University", "url": url_for("university.dashboard")},
                    {"name": "Admin Dashboard", "url": url_for("admin.dashboard")},
                    {"name": "SAS AI", "url": url_for("ai.chat")},
                ])
            else:
                # Non-admin users - check role and show appropriate modules
                user_role_names = [r.name for r in current_user.roles.all()]
                user_role_obj_name = current_user.role_obj.name if current_user.role_obj else None
                all_user_roles = user_role_names + ([user_role_obj_name] if user_role_obj_name else [])
                
                # Check if user has specific role
                def has_role(*role_names):
                    return any(r in all_user_roles for r in role_names)
                
                # Show Accounting modules for ACCOUNTING role
                if has_role('ACCOUNTING'):
                    modules.append({
                        "name": "Accounting Department",
                        "url": url_for("accounting.dashboard"),
                        "children": [
                            {"name": "Accounting Overview", "url": url_for("accounting.dashboard")},
                            {"name": "Receipting System", "url": url_for("accounting.receipts_list")},
                            {"name": "Quotations", "url": url_for("quotes.list_quotes")},
                            {"name": "Invoices", "url": url_for("invoices.invoice_list")},
                            {"name": "Cashbook", "url": url_for("cashbook.index")},
                            {"name": "Financial Reports", "url": url_for("reports.reports_index")},
                            {"name": "Payroll Management", "url": url_for("payroll.payroll_list")},
                        ]
                    })
                
                # These modules are available to all authenticated users
                modules.append({"name": "Employee University", "url": url_for("university.dashboard")})
                modules.append({"name": "SAS AI", "url": url_for("ai.chat")})
                modules.append({"name": "Announcements", "url": url_for("communication.announcements_list")})
        
        return dict(modules=modules, format_millions=format_millions, has_any_permission=has_any_permission)
    
    # TEMPORARILY DISABLED: Template context processor for permissions
    # @app.context_processor
    # def inject_permissions():
    #     from sas_management.utils.permissions import has_permission
    #     return dict(has_permission=has_permission)
    # @app.context_processor
    # def inject_permissions():
    #     from sas_management.utils.permissions import has_permission
    #     return dict(has_permission=has_permission)
    
    # Global error handler - only show tracebacks in debug mode
    import traceback
    from flask import Response
    from werkzeug.exceptions import HTTPException
    
    @app.errorhandler(Exception)
    def handle_exception(e):
        # Pass through HTTP exceptions (like 404) to Flask's default handlers
        if isinstance(e, HTTPException):
            return e
        
        tb = traceback.format_exc()
        
        # Always log to file
        try:
            app.logger.error("Unhandled exception:\n" + tb)
        except:
            pass  # Don't fail if logging fails
        
        # Only show traceback in browser if DEBUG mode is enabled
        if app.config.get('DEBUG', False):
            print("\n====== FULL ERROR TRACEBACK ======\n")
            print(tb)
            print("==================================\n")
            return Response(f"<pre style='background:#1e1e1e;color:#d4d4d4;padding:20px;font-family:monospace;white-space:pre-wrap;'>{tb}</pre>", mimetype="text/html"), 500
        else:
            # Production: show generic error page
            return Response("<h1>Internal Server Error</h1><p>An error occurred. Please contact support.</p>", mimetype="text/html"), 500
    
    # Specific 500 error handler
    @app.errorhandler(500)
    def handle_500(e):
        if app.config.get('DEBUG', False):
            import traceback
            tb = traceback.format_exc()
            return f"<pre>{tb}</pre>", 500
        else:
            return "<h1>Internal Server Error</h1><p>An error occurred. Please contact support.</p>", 500
    
    # All blueprints registered via register_blueprints() above

    with app.app_context():
        # AI directories creation TEMPORARILY DISABLED
        # ai_assets_dir = os.path.join(app.instance_path, "ai_assets")
        # ai_models_dir = os.path.join(app.instance_path, "ai_models")
        # os.makedirs(ai_assets_dir, exist_ok=True)
        # os.makedirs(ai_models_dir, exist_ok=True)
        
        # CRITICAL FIX: Fix service_events.title column (runs once per startup)
        try:
            import sys
            import sqlite3
            # Add scripts directory to path for import
            base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            scripts_dir = os.path.join(base_dir, "scripts")
            if scripts_dir not in sys.path:
                sys.path.insert(0, scripts_dir)
            
            try:
                from db_autofix.fix_service_events_schema import fix_service_events_title_column
                # Pass the actual database path from app config
                db_path = os.path.join(app.instance_path, "sas.db")
                success, message = fix_service_events_title_column(db_path=db_path)
                if success:
                    print(message)
                    app.logger.info(f"Schema fix: {message}")
                else:
                    app.logger.warning(f"Schema fix warning: {message}")
                    print(f"[WARNING] {message}")
            except ImportError:
                # Fallback: direct SQL execution if import fails
                db_path = os.path.join(app.instance_path, "sas.db")
                if os.path.exists(db_path):
                    conn = sqlite3.connect(db_path)
                    cursor = conn.cursor()
                    # Check if service_events table exists
                    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='service_events'")
                    if cursor.fetchone():
                        # Check if column exists
                        cursor.execute("PRAGMA table_info(service_events)")
                        columns = [row[1] for row in cursor.fetchall()]
                        if "title" not in columns:
                            cursor.execute("ALTER TABLE service_events ADD COLUMN title TEXT")
                            conn.commit()
                            print("[FIX] service_events.title added (fallback method)")
                            app.logger.info("Schema fix: service_events.title added (fallback)")
                        else:
                            print("[OK] service_events.title already exists")
                    conn.close()
        except Exception as e:
            # Don't crash app if migration fails
            app.logger.warning(f"Schema fix error (non-fatal): {e}")
            print(f"[WARNING] Schema fix skipped: {e}")
        
        # SINGLE DATABASE AUTO-FIX SYSTEM - Runs once at startup within app context
        # This consolidates all auto-heal and auto-fix logic into one place
        db_path = os.path.join(app.instance_path, "sas.db")
        validation_result = None
        try:
            # Use auto_fix_schema as the primary auto-fix mechanism
            # It handles missing columns and schema synchronization
            from scripts.db_autofix.auto_fix import auto_fix_schema, print_health_banner
            validation_result = auto_fix_schema(db_path=db_path, app=app)
            
            # Print health banner at startup (only once)
            if validation_result:
                print_health_banner(validation_result)
                
                # Log critical issues
                if validation_result.critical_missing:
                    app.logger.error(
                        f"Schema validation FAILED: {len(validation_result.critical_missing)} critical columns missing. "
                        f"Tables affected: {', '.join(set(t for t, _ in validation_result.critical_missing))}"
                    )
                elif validation_result.failed_fixes:
                    app.logger.error(
                        f"Auto-fix FAILED: {len(validation_result.failed_fixes)} column additions failed. "
                        f"See startup banner for details."
                    )
                elif validation_result.non_critical_missing:
                    app.logger.warning(
                        f"Schema validation: {len(validation_result.non_critical_missing)} non-critical columns missing. "
                        f"Schema is functional but may need manual migration."
                    )
        except Exception as e:
            error_msg = f"Database auto-fix ERROR: {e}"
            app.logger.error(error_msg)
            print(f"[ERROR] {error_msg}")
            if app.config.get("ENV") != "production":
                import traceback
                traceback.print_exc()
            # Create a failed validation result
            from scripts.db_autofix.auto_fix import SchemaValidationResult
            validation_result = SchemaValidationResult()
            validation_result.is_valid = False
            validation_result.failed_fixes.append(("SYSTEM", "auto_fix", str(e)))
        
        # Import AIFeature model to ensure it's registered with SQLAlchemy
        try:
            from sas_management.ai.models import AIFeature
        except Exception as e:
            app.logger.warning(f"Error importing AIFeature model: {e}")
        
        # Create all tables
        db.create_all()
        
        # CRITICAL FIX: Fix ai_features table schema (runs once per startup BEFORE seeding)
        try:
            import sys
            import sqlite3
            # Add scripts directory to path for import
            base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            scripts_dir = os.path.join(base_dir, "scripts")
            if scripts_dir not in sys.path:
                sys.path.insert(0, scripts_dir)
            
            try:
                from db_autofix.fix_ai_features_table import fix_ai_features_table
                # Pass the actual database path from app config
                db_path = os.path.join(app.instance_path, "sas.db")
                success, message = fix_ai_features_table(db_path=db_path)
                if success:
                    print(message)
                    app.logger.info(f"AI features schema fix: {message}")
                else:
                    app.logger.warning(f"AI features schema fix warning: {message}")
                    print(f"[WARNING] {message}")
            except ImportError:
                # Fallback: direct SQL execution if import fails
                db_path = os.path.join(app.instance_path, "sas.db")
                if os.path.exists(db_path):
                    conn = sqlite3.connect(db_path)
                    cursor = conn.cursor()
                    # Check if ai_features table exists
                    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='ai_features'")
                    if cursor.fetchone():
                        # Check if key column exists
                        cursor.execute("PRAGMA table_info(ai_features)")
                        columns = [row[1] for row in cursor.fetchall()]
                        if "key" not in columns:
                            cursor.execute("ALTER TABLE ai_features ADD COLUMN key TEXT")
                            conn.commit()
                            print("[FIX] ai_features.key added (fallback method)")
                            app.logger.info("AI features schema fix: key column added (fallback)")
                        else:
                            print("[OK] ai_features.key already exists")
                    conn.close()
        except Exception as e:
            # Don't crash app if migration fails
            app.logger.warning(f"AI features schema fix error (non-fatal): {e}")
            print(f"[WARNING] AI features schema fix skipped: {e}")
        
        # Auto-seed AI features (runs once on app start if empty)
        try:
            from sas_management.ai.models import ensure_default_ai_features
            ensure_default_ai_features()
        except Exception as e:
            app.logger.warning(f"Error ensuring default AI features: {e}")
        
        # Seed initial data
        seed_initial_data(db)
        
        # Ensure all required roles exist
        try:
            from sas_management.utils.role_utils import ensure_roles_exist
            roles_created = ensure_roles_exist()
            if roles_created > 0:
                app.logger.info(f"Created {roles_created} missing system roles.")
        except Exception as e:
            app.logger.warning(f"Error ensuring roles exist: {e}")
        
        # Check and revert expired temporary roles
        try:
            from sas_management.utils.role_utils import check_expired_roles
            reverted_count = check_expired_roles()
            if reverted_count > 0:
                app.logger.info(f"Reverted {reverted_count} expired temporary role assignments.")
        except Exception as e:
            app.logger.warning(f"Error checking expired roles: {e}")
        
        # Configure relationship ordering (must be after all models are defined and mapped)
        # This ensures all relationships are properly configured
        try:
            from sas_management.models import configure_relationship_ordering
            configure_relationship_ordering()
        except Exception as e:
            # Log but don't fail - relationships should work without this
            if app.config.get("ENV") != "production":
                print(f"[WARNING] Relationship ordering configuration warning: {e}")
        
        # Set up audit logging
        from sas_management.models import setup_audit_logging
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

    # Global template context (temporarily disabled in safe mode)
    #     # TEMPORARILY DISABLED: All context processors to prevent global errors
    # @app.context_processor
    # def inject_globals():
    #     from flask_login import current_user
    #     from sas_management.models import UserRole
    #     
    #     # Safe check for Employee University availability
    #     # Only show to authenticated admin users
    #     show_employee_university = False
    #     if hasattr(current_user, 'is_authenticated') and current_user.is_authenticated:
    #         try:
    #             # Check if user is admin
    #             is_admin = False
    #             if hasattr(current_user, 'is_super_admin') and current_user.is_super_admin():
    #                 is_admin = True
    #             elif hasattr(current_user, 'role') and current_user.role == UserRole.Admin:
    #                 is_admin = True
    #             
    #             if is_admin:
    #                 # Check if blueprint exists
    #                 from sas_management.blueprints.university import university_bp
    #                 show_employee_university = True
    #         except Exception:
    #             show_employee_university = False
    #     
    #     return {
    #         "show_employee_university": show_employee_university,
    #         "CURRENCY": app.config.get("CURRENCY_PREFIX", "UGX "),
    #         "date": date
    #     }
    # 
    # @app.context_processor
    # def inject_modules():
    #     try:
    #         from sas_management.navigation.modules import get_modules
    #         return {'modules': get_modules()}
    #     except Exception:
    #         return {'modules': []}
    # 
    # @app.context_processor
    # def inject_config():
    #     """Make app config available in all templates."""
    #     # Add SAS_AI_ENABLED as alias for AI_MODULE_ENABLED for template compatibility
    #     class ConfigWrapper:
    #         def __init__(self, config_obj):
    #             self._config = config_obj
    #         def get(self, key, default=None):
    #             # Handle aliases
    #             if key == 'SAS_AI_ENABLED':
    #                 return self._config.get('AI_MODULE_ENABLED', default if default is not None else True)
    #             return self._config.get(key, default)
    #         def __getitem__(self, key):
    #             if key == 'SAS_AI_ENABLED':
    #                 return self._config.get('AI_MODULE_ENABLED', True)
    #             return self._config[key]
    #         def __getattr__(self, key):
    #             if key == 'SAS_AI_ENABLED':
    #                 return self._config.get('AI_MODULE_ENABLED', True)
    #             return getattr(self._config, key)
    #     return {'config': ConfigWrapper(app.config)}

    # Load system tester if available (for health checks)
    try:
        from tools.system_tester import run_full_test
        # Test can be run manually via: python tools/system_tester.py
    except ImportError:
        pass  # System tester is optional
    
    # Debug routes (only in development)
    @app.route('/debug/modules')
    def debug_modules():
        try:
            from sas_management.navigation.modules import get_modules
            return {'loaded_modules': get_modules()}
        except Exception as e:
            return {'error': str(e)}

    @app.route('/debug/find-nav')
    def debug_find_nav():
        import inspect
        import sas_management

        results = {}

        # Scan all attributes in the package
        for name in dir(sas_management):
            obj = getattr(sas_management, name)
            if callable(obj):
                try:
                    source = inspect.getsource(obj)
                    if 'module' in source.lower() or 'nav' in source.lower():
                        results[name] = source
                except:
                    pass

        return results
    
    return app


@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))


# Create app instance for direct execution and gunicorn compatibility
app = create_app()


if __name__ == "__main__":
    import os
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
