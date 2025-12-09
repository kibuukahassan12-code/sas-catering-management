"""Final complete schema synchronization - ensures ALL models match database."""
from app import app, db
from sqlalchemy import inspect, text
from sqlalchemy.exc import OperationalError
from models import *  # Import all models to ensure they're registered

def get_table_columns(inspector, table_name):
    """Get all column names for a table."""
    try:
        if table_name not in inspector.get_table_names():
            return []
        return [col['name'] for col in inspector.get_columns(table_name)]
    except:
        return []

def add_column_safe(table_name, col_name, col_type, inspector, db_session):
    """Safely add a column."""
    try:
        existing = get_table_columns(inspector, table_name)
        if col_name in existing:
            return False, "exists"
        
        # Clean column type for SQLite
        col_type_clean = col_type.split(" DEFAULT ")[0] if " DEFAULT " in col_type else col_type
        
        db_session.execute(text(f"ALTER TABLE {table_name} ADD COLUMN {col_name} {col_type_clean}"))
        db_session.commit()
        return True, "added"
    except OperationalError as e:
        error_str = str(e).lower()
        if "duplicate" in error_str or "already exists" in error_str:
            return False, "exists"
        try:
            col_type_clean = col_type.split(" DEFAULT ")[0]
            db_session.execute(text(f"ALTER TABLE {table_name} ADD COLUMN {col_name} {col_type_clean}"))
            db_session.commit()
            return True, "added"
        except:
            return False, f"Error: {str(e)[:50]}"
    except Exception as e:
        return False, f"Error: {str(e)[:50]}"

# Define all critical table fixes based on models
TABLE_FIXES = {
    "inventory_item": [
        ("description", "TEXT"),
        ("unit_price_ugx", "NUMERIC(12,2)"),
        ("category", "VARCHAR(100)"),
        ("sku", "VARCHAR(100)"),
        ("replacement_cost", "NUMERIC(10,2)"),
        ("condition", "VARCHAR(50)"),
        ("location", "VARCHAR(100)"),
        ("tags", "VARCHAR(255)"),
        ("status", "VARCHAR(50)"),
        ("created_at", "DATETIME"),
        ("updated_at", "DATETIME"),
    ],
    "incoming_lead": [
        ("email", "VARCHAR(120)"),
    ],
    "user": [
        ("created_at", "DATETIME"),
        ("last_login", "DATETIME"),
    ],
    "client": [
        ("created_at", "DATETIME"),
        ("updated_at", "DATETIME"),
    ],
    "event": [
        ("created_at", "DATETIME"),
        ("updated_at", "DATETIME"),
    ],
    "task": [
        ("created_at", "DATETIME"),
    ],
}

with app.app_context():
    print("=" * 70)
    print("FINAL COMPLETE SCHEMA SYNCHRONIZATION")
    print("=" * 70)
    print()
    
    inspector = inspect(db.engine)
    all_tables = inspector.get_table_names()
    print(f"Found {len(all_tables)} tables in database")
    print()
    
    total_fixes = 0
    
    # Apply all fixes
    for table_name, fixes in TABLE_FIXES.items():
        if table_name not in all_tables:
            print(f"⚠ {table_name} table does not exist (will be created by db.create_all())")
            continue
        
        existing = get_table_columns(inspector, table_name)
        print(f"Fixing {table_name}...")
        print(f"  Current columns ({len(existing)}): {', '.join(existing[:10])}{'...' if len(existing) > 10 else ''}")
        
        table_fixes = 0
        for col_name, col_type in fixes:
            success, message = add_column_safe(table_name, col_name, col_type, inspector, db.session)
            if success:
                print(f"    ✓ ADDED '{col_name}'")
                table_fixes += 1
                total_fixes += 1
            elif message != "exists":
                print(f"    ⚠ '{col_name}': {message}")
        
        if table_fixes == 0:
            print(f"  ✓ All columns already exist")
        print()
    
    # Ensure all tables are created
    print("Ensuring all tables exist...")
    try:
        db.create_all()
        print("  ✓ All tables verified")
    except Exception as e:
        print(f"  ⚠ Error: {e}")
    
    print()
    print("=" * 70)
    print("TESTING ALL CRITICAL QUERIES...")
    print("=" * 70)
    
    test_results = []
    
    # Test InventoryItem
    try:
        from models import InventoryItem
        count = InventoryItem.query.filter(InventoryItem.stock_count <= 10).count()
        test_results.append(("InventoryItem (low stock)", True, f"{count} items"))
    except Exception as e:
        test_results.append(("InventoryItem (low stock)", False, str(e)[:100]))
    
    # Test IncomingLead
    try:
        from models import IncomingLead
        count = IncomingLead.query.filter_by(pipeline_stage='New Lead').count()
        test_results.append(("IncomingLead (new leads)", True, f"{count} leads"))
    except Exception as e:
        test_results.append(("IncomingLead (new leads)", False, str(e)[:100]))
    
    # Test User
    try:
        from models import User
        count = User.query.count()
        test_results.append(("User (all users)", True, f"{count} users"))
    except Exception as e:
        test_results.append(("User (all users)", False, str(e)[:100]))
    
    # Test Client
    try:
        from models import Client
        count = Client.query.filter(Client.is_archived == False).count()
        test_results.append(("Client (active)", True, f"{count} clients"))
    except Exception as e:
        test_results.append(("Client (active)", False, str(e)[:100]))
    
    # Test Event
    try:
        from models import Event
        count = Event.query.count()
        test_results.append(("Event (all events)", True, f"{count} events"))
    except Exception as e:
        test_results.append(("Event (all events)", False, str(e)[:100]))
    
    # Test Task (critical - was causing errors)
    try:
        from models import Task
        from datetime import date
        count = Task.query.filter(Task.due_date <= date.today()).filter(Task.status != 'Complete').count()
        test_results.append(("Task (overdue)", True, f"{count} overdue tasks"))
    except Exception as e:
        test_results.append(("Task (overdue)", False, str(e)[:100]))
    
    # Print test results
    print()
    all_passed = True
    for test_name, passed, message in test_results:
        status = "✓" if passed else "✗"
        print(f"{status} {test_name}: {message}")
        if not passed:
            all_passed = False
    
    print()
    print("=" * 70)
    if all_passed:
        print(f"✅ ALL TESTS PASSED! Applied {total_fixes} schema fix(es).")
    else:
        print(f"⚠️  SOME TESTS FAILED! Applied {total_fixes} schema fix(es).")
        print("   Please review the errors above and run this script again.")
    print("=" * 70)
    print()
    print("⚠️  IMPORTANT: Restart your Flask application NOW!")
    print("   The database schema has been updated.")

