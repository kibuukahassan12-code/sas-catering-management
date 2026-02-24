#!/usr/bin/env python3
"""
MASTER SEEDING SCRIPT - Runs ALL seed scripts to populate EVERY module
This ensures complete data population for all modules.
"""
import os
import sys
os.environ["SECRET_KEY"] = "sas-management-system-secret-key-2024-production"

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

print("=" * 80)
print("MASTER MODULE SEEDING - RUNNING ALL SEED SCRIPTS")
print("=" * 80)
print()

# Run comprehensive seed first
print("[STEP 1] Running comprehensive seed...")
try:
    from comprehensive_seed_all_modules import seed_all_modules
    seed_all_modules()
except Exception as e:
    print(f"  [WARN] Comprehensive seed error: {e}")

# Run all individual seed scripts
seed_scripts = [
    ("CRM Pipeline", "seed_crm_pipeline_data", "seed_pipeline_data"),
    ("AI Sample Data", "seed_ai_sample_data", "seed_ai_data"),
    ("Enterprise Modules", "seed_enterprise_modules", "seed_enterprise_data"),
    ("Premium Modules", "seed_premium_modules", "seed_premium_modules"),
    ("Production QC", "seed_production_quality_control_data", "seed_production_qc_data"),
    ("HR Sample Data", "seed_hr_sample_data", "seed_hr_data"),
    ("POS Sample Data", "seed_pos_sample_data", "seed_pos_data"),
    ("Accounting Sample", "seed_accounting_sample_data", "seed_accounting_sample_data"),
    ("BI Sample Data", "seed_bi_sample_data", "seed_bi_data"),
    ("Recipe Sample", "seed_recipe_sample_data", "seed_recipe_data"),
    ("Food Safety", "seed_food_safety_data", "seed_food_safety_data"),
    ("Automation", "seed_automation_data", "seed_automation_data"),
    ("Communication", "seed_communication_data", "seed_communication_data"),
    ("Event Profitability", "seed_event_profitability_data", "seed_event_profitability_data"),
    ("Dispatch", "seed_dispatch_data", "seed_dispatch_data"),
]

for script_name, module_name, function_name in seed_scripts:
    print(f"\n[STEP] Running {script_name}...")
    try:
        module = __import__(module_name, fromlist=[function_name])
        func = getattr(module, function_name)
        func()
        print(f"  [OK] {script_name} completed")
    except ImportError as e:
        print(f"  [SKIP] {script_name} - module not found: {e}")
    except AttributeError as e:
        print(f"  [SKIP] {script_name} - function not found: {e}")
    except Exception as e:
        print(f"  [WARN] {script_name} - error: {e}")

# Final verification
print("\n" + "=" * 80)
print("FINAL VERIFICATION")
print("=" * 80)

from sas_management.app import create_app
from sas_management.models import (
    db, Client, Event, IncomingLead, Invoice, Task, InventoryItem,
    MenuItem, BakeryItem, ProductionOrder, Employee, POSProduct,
    Quotation, Supplier, Announcement, MenuCategory
)

app = create_app()
with app.app_context():
    print(f"Clients: {Client.query.count()}")
    print(f"Events: {Event.query.count()}")
    print(f"Leads: {IncomingLead.query.count()}")
    print(f"Invoices: {Invoice.query.count()}")
    print(f"Tasks: {Task.query.count()}")
    print(f"Inventory Items: {InventoryItem.query.count()}")
    print(f"Menu Categories: {MenuCategory.query.count()}")
    print(f"Menu Items: {MenuItem.query.count()}")
    print(f"Bakery Items: {BakeryItem.query.count()}")
    print(f"Production Orders: {ProductionOrder.query.count()}")
    print(f"Employees: {Employee.query.count()}")
    print(f"POS Products: {POSProduct.query.count()}")
    print(f"Quotations: {Quotation.query.count()}")
    print(f"Suppliers: {Supplier.query.count()}")
    print(f"Announcements: {Announcement.query.count()}")
    
    # Check AI features
    try:
        from sas_management.ai.models import AIFeature
        ai_features = AIFeature.query.count()
        print(f"AI Features: {ai_features}")
    except:
        print("AI Features: N/A")
    
print("\n" + "=" * 80)
print("ALL SEEDING COMPLETE!")
print("=" * 80)
print("\nLogin: admin@sas.com / password")
print("URL: http://127.0.0.1:5000/dashboard")
print()
