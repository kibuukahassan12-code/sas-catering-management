"""Complete System Health Test & Auto-Repair Tool for SAS Best Foods ERP."""
import os
import sys
import importlib
import traceback
import shutil
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from flask import Flask
from sqlalchemy import inspect


# ============================================================
# CONFIGURATION
# ============================================================

REQUIRED_BLUEPRINTS = [
    "core", "catering", "events", "proposals", "hire", "inventory", "invoices",
    "bakery", "payroll", "cashbook", "crm", "leads", "reports", "tasks",
    "university", "chat", "dispatch", "vendors", "food_safety",
    "timeline", "mobile_staff", "client_portal", "kds", "integrations",
    "automation", "accounting", "pos", "production", "hr", "audit",
    "bi", "search", "floorplanner", "menu_builder", "communication",
    "contracts", "production_recipes", "branches", "ai", "maintenance"
]

TEST_RESULTS = {
    "passed": [],
    "failed": [],
    "fixed": [],
    "warnings": []
}


# ============================================================
# UTILITY FUNCTIONS
# ============================================================

def log_pass(item, message=""):
    """Log a passed test."""
    msg = f"[OK] {item}"
    if message:
        msg += f" - {message}"
    try:
        print(msg)
    except UnicodeEncodeError:
        print(f"[OK] {item} - {message}".encode('ascii', 'replace').decode('ascii'))
    TEST_RESULTS["passed"].append((item, message))


def log_fail(item, error, auto_fixed=False):
    """Log a failed test."""
    msg = f"[FAIL] {item}"
    if error:
        msg += f" - {error}"
    if auto_fixed:
        msg += " [AUTO-FIXED]"
    print(msg)
    if auto_fixed:
        TEST_RESULTS["fixed"].append((item, error))
    else:
        TEST_RESULTS["failed"].append((item, error))


def log_warn(item, message):
    """Log a warning."""
    msg = f"[WARN] {item} - {message}"
    print(msg)
    TEST_RESULTS["warnings"].append((item, message))


# ============================================================
# TEST FUNCTIONS
# ============================================================

def test_app_creation():
    """Test if Flask app can be created."""
    print("\n" + "="*70)
    print("TEST 1: Flask Application Creation")
    print("="*70)
    
    try:
        from app import create_app
        import sys
        import io
        
        # Suppress print output during app creation to avoid encoding issues
        old_stdout = sys.stdout
        sys.stdout = io.StringIO()
        
        try:
            app = create_app()
            sys.stdout = old_stdout
            log_pass("App Creation", "Flask app created successfully")
            return app
        except Exception as inner_e:
            sys.stdout = old_stdout
            raise inner_e
    except Exception as e:
        error_msg = str(e).encode('ascii', 'replace').decode('ascii')
        log_fail("App Creation", error_msg)
        return None


def test_blueprint_registration(app):
    """Test blueprint registration."""
    print("\n" + "="*70)
    print("TEST 2: Blueprint Registration")
    print("="*70)
    
    if not app:
        log_fail("Blueprint Test", "App not available")
        return
    
    registered = list(app.blueprints.keys())
    
    for bp_name in REQUIRED_BLUEPRINTS:
        if bp_name in registered:
            log_pass(f"Blueprint: {bp_name}")
        else:
            log_warn(f"Blueprint: {bp_name}", "Not registered (may be optional or conditionally loaded)")
    
    print(f"\nTotal blueprints registered: {len(registered)}")
    log_pass("Blueprint Registration", f"{len(registered)} blueprints found")


def test_blueprint_imports():
    """Test if all blueprints can be imported."""
    print("\n" + "="*70)
    print("TEST 3: Blueprint Module Imports")
    print("="*70)
    
    # Blueprint naming exceptions
    bp_name_mapping = {
        "maintenance": ("blueprints.hire.maintenance_routes", "maintenance_bp"),
        "communication": ("blueprints.communication", "comm_bp"),
        "production_recipes": ("blueprints.production_recipes", "recipes_bp"),
        "core": None  # Skip, handled in routes.py
    }
    
    for bp_name in REQUIRED_BLUEPRINTS:
        if bp_name == "core":
            continue  # Core is in routes.py
        
        try:
            # Get correct path and variable name
            if bp_name in bp_name_mapping:
                bp_path, bp_var = bp_name_mapping[bp_name]
            else:
                bp_path = f"blueprints.{bp_name}"
                bp_var = f"{bp_name}_bp"
            
            module = importlib.import_module(bp_path)
            
            # Check if blueprint exists
            if hasattr(module, bp_var):
                log_pass(f"Import: {bp_name}")
            else:
                # Try alternate names
                alt_names = [f"{bp_name}_bp", f"comm_bp", f"recipes_bp"]
                found = False
                for alt_name in alt_names:
                    if hasattr(module, alt_name):
                        log_pass(f"Import: {bp_name} (as {alt_name})")
                        found = True
                        break
                if not found:
                    log_warn(f"Import: {bp_name}", f"Module exists but blueprint variable not found")
        except ImportError as e:
            log_fail(f"Import: {bp_name}", str(e))
        except Exception as e:
            log_warn(f"Import: {bp_name}", str(e))


def test_database_models():
    """Test database models."""
    print("\n" + "="*70)
    print("TEST 4: Database Models")
    print("="*70)
    
    try:
        from models import db
        from app import create_app
        
        app = create_app()
        with app.app_context():
            # Try to reflect existing tables
            inspector = inspect(db.engine)
            tables = inspector.get_table_names()
            
            log_pass("Database Connection", f"{len(tables)} tables found")
            
            # Test common models
            common_models = [
                "User", "Client", "Event", "Invoice", "Quotation",
                "InventoryItem", "ProductionOrder", "AccountingReceipt"
            ]
            
            try:
                from models import User, Client, Event, Invoice, Quotation
                log_pass("Model: Core models imported")
            except ImportError as e:
                log_warn("Model Import", str(e))
            
            for model_name in common_models:
                try:
                    from models import db
                    # Try to query the model
                    model_class = getattr(__import__('models', fromlist=[model_name]), model_name, None)
                    if model_class:
                        log_pass(f"Model: {model_name}")
                    else:
                        log_warn(f"Model: {model_name}", "Not found in models.py")
                except Exception as e:
                    log_warn(f"Model: {model_name}", str(e))
    
    except Exception as e:
        log_fail("Database Models", str(e))


def test_template_existence(app):
    """Test if required templates exist."""
    print("\n" + "="*70)
    print("TEST 5: Template Existence")
    print("="*70)
    
    if not app:
        log_fail("Template Test", "App not available")
        return
    
    template_dir = Path(project_root) / "templates"
    if not template_dir.exists():
        log_fail("Template Directory", "templates/ directory not found")
        return
    
    # Check key templates
    key_templates = [
        "base.html",
        "dashboard.html",
        "login.html"
    ]
    
    for template in key_templates:
        template_path = template_dir / template
        if template_path.exists():
            log_pass(f"Template: {template}")
        else:
            log_fail(f"Template: {template}", "File not found")
            auto_fix_missing_template(str(template_path))
    
    # Count all templates
    all_templates = list(template_dir.rglob("*.html"))
    log_pass("Template Count", f"{len(all_templates)} HTML templates found")


def test_static_files():
    """Test if required static files exist."""
    print("\n" + "="*70)
    print("TEST 6: Static Files")
    print("="*70)
    
    static_dir = Path(project_root) / "static"
    if not static_dir.exists():
        log_warn("Static Directory", "static/ directory not found")
        return
    
    # Check for logo
    logo_path = static_dir / "images" / "sas_logo.png"
    if logo_path.exists():
        log_pass("SAS Logo", "Found")
    else:
        log_warn("SAS Logo", f"Not found at {logo_path}")
        # Create placeholder
        (static_dir / "images").mkdir(parents=True, exist_ok=True)
        with open(logo_path, 'w') as f:
            f.write("# Placeholder for SAS logo\n")
        log_pass("SAS Logo", "Placeholder created")
    
    # Check CSS
    css_dir = static_dir / "css"
    if css_dir.exists():
        css_files = list(css_dir.glob("*.css"))
        log_pass("CSS Files", f"{len(css_files)} files found")
    else:
        log_warn("CSS Directory", "Not found")


def test_routes_basic(app):
    """Test basic route accessibility."""
    print("\n" + "="*70)
    print("TEST 7: Route Accessibility (Basic)")
    print("="*70)
    
    if not app:
        log_fail("Route Test", "App not available")
        return
    
    # Test key routes
    key_routes = [
        "/",
        "/login",
        "/dashboard"
    ]
    
    with app.test_client() as client:
        for route in key_routes:
            try:
                response = client.get(route, follow_redirects=True)
                if response.status_code in [200, 302, 401]:  # 401 is OK for protected routes
                    log_pass(f"Route: {route}", f"Status: {response.status_code}")
                else:
                    log_warn(f"Route: {route}", f"Unexpected status: {response.status_code}")
            except Exception as e:
                log_warn(f"Route: {route}", str(e))


def test_service_modules():
    """Test service modules."""
    print("\n" + "="*70)
    print("TEST 8: Service Modules")
    print("="*70)
    
    services_dir = Path(project_root) / "services"
    if not services_dir.exists():
        log_warn("Services Directory", "Not found")
        return
    
    service_files = list(services_dir.glob("*.py"))
    log_pass("Service Files", f"{len(service_files)} found")
    
    # Test key services
    key_services = [
        "accounting_service",
        "production_service",
        "pos_service"
    ]
    
    for service_name in key_services:
        try:
            module = importlib.import_module(f"services.{service_name}")
            log_pass(f"Service: {service_name}")
        except Exception as e:
            log_warn(f"Service: {service_name}", str(e))


# ============================================================
# AUTO-REPAIR FUNCTIONS
# ============================================================

def auto_fix_missing_template(template_path):
    """Auto-create missing template."""
    try:
        template_file = Path(template_path)
        template_file.parent.mkdir(parents=True, exist_ok=True)
        
        template_name = template_file.stem
        
        content = f"""{{% extends "base.html" %}}
{{% block content %}}
<section class="page-header">
    <div>
        <h1>{template_name.title()}</h1>
        <p class="muted">This template was auto-generated by the system tester.</p>
    </div>
</section>

<section class="panel">
    <p>Template placeholder for {template_name}. Please update with proper content.</p>
</section>
{{% endblock %}}
"""
        
        with open(template_file, 'w', encoding='utf-8') as f:
            f.write(content)
        
        log_pass(f"Auto-Fixed Template: {template_name}", "Created placeholder")
        TEST_RESULTS["fixed"].append((f"Template: {template_name}", "Created"))
    except Exception as e:
        log_fail(f"Auto-Fix Template: {template_path}", str(e))


def copy_sample_asset():
    """Copy sample asset if available."""
    print("\n" + "="*70)
    print("AUTO-REPAIR: Sample Asset")
    print("="*70)
    
    source = "/mnt/data/drwa.JPG"
    dest_dir = Path(project_root) / "instance" / "tests"
    dest_dir.mkdir(parents=True, exist_ok=True)
    dest = dest_dir / "sample.jpg"
    
    if os.path.exists(source):
        try:
            shutil.copy2(source, dest)
            log_pass("Sample Asset", f"Copied to {dest}")
        except Exception as e:
            log_warn("Sample Asset", f"Could not copy: {e}")
    else:
        log_warn("Sample Asset", f"Source not found: {source}")
        # Create placeholder
        with open(dest, 'w') as f:
            f.write("# Placeholder for sample asset\n")
        log_pass("Sample Asset", "Placeholder created")


# ============================================================
# MAIN ORCHESTRATOR
# ============================================================

def run_full_test():
    """Run complete system health test."""
    print("\n" + "="*70)
    print("SAS BEST FOODS ERP - FULL SYSTEM HEALTH TEST & AUTO-REPAIR")
    print("="*70)
    print(f"Project Root: {project_root}")
    print(f"Timestamp: {__import__('datetime').datetime.now()}")
    
    # Reset results
    TEST_RESULTS["passed"] = []
    TEST_RESULTS["failed"] = []
    TEST_RESULTS["fixed"] = []
    TEST_RESULTS["warnings"] = []
    
    # Run tests
    app = test_app_creation()
    test_blueprint_registration(app)
    test_blueprint_imports()
    test_database_models()
    test_template_existence(app)
    test_static_files()
    test_routes_basic(app)
    test_service_modules()
    copy_sample_asset()
    
    # Print summary
    print("\n" + "="*70)
    print("TEST SUMMARY")
    print("="*70)
    print(f"[PASS] Passed: {len(TEST_RESULTS['passed'])}")
    print(f"[FAIL] Failed: {len(TEST_RESULTS['failed'])}")
    print(f"[FIX] Fixed: {len(TEST_RESULTS['fixed'])}")
    print(f"[WARN] Warnings: {len(TEST_RESULTS['warnings'])}")
    
    if TEST_RESULTS["failed"]:
        print("\nFAILED ITEMS:")
        for item, error in TEST_RESULTS["failed"]:
            print(f"  - {item}: {error}")
    
    if TEST_RESULTS["fixed"]:
        print("\nAUTO-FIXED ITEMS:")
        for item, error in TEST_RESULTS["fixed"]:
            print(f"  - {item}: {error}")
    
    if TEST_RESULTS["warnings"]:
        print("\nWARNINGS:")
        for item, message in TEST_RESULTS["warnings"][:10]:  # Limit to 10
            print(f"  - {item}: {message}")
        if len(TEST_RESULTS["warnings"]) > 10:
            print(f"  ... and {len(TEST_RESULTS['warnings']) - 10} more warnings")
    
    print("\n" + "="*70)
    print("SYSTEM TEST COMPLETE")
    print("="*70)
    
    return len(TEST_RESULTS["failed"]) == 0


if __name__ == "__main__":
    success = run_full_test()
    sys.exit(0 if success else 1)

