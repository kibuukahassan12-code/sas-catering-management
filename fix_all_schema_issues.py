"""Ultimate schema fix - checks and fixes ALL models against database."""
from app import app, db
from sqlalchemy import inspect, text
from sqlalchemy.exc import OperationalError
from datetime import datetime

def get_table_columns(inspector, table_name):
    """Get all column names for a table."""
    try:
        if table_name not in inspector.get_table_names():
            return []
        return [col['name'] for col in inspector.get_columns(table_name)]
    except:
        return []

def add_column_safe(table_name, col_name, col_type, inspector, db_session):
    """Safely add a column, handling all error cases."""
    try:
        existing = get_table_columns(inspector, table_name)
        if col_name in existing:
            return False, "exists"
        
        # Remove DEFAULT clause if present for SQLite compatibility
        col_type_clean = col_type.split(" DEFAULT ")[0] if " DEFAULT " in col_type else col_type
        
        db_session.execute(text(f"ALTER TABLE {table_name} ADD COLUMN {col_name} {col_type_clean}"))
        db_session.commit()
        return True, "added"
    except OperationalError as e:
        error_str = str(e).lower()
        if "duplicate" in error_str or "already exists" in error_str:
            return False, "exists"
        # Try again without DEFAULT
        try:
            col_type_clean = col_type.split(" DEFAULT ")[0]
            db_session.execute(text(f"ALTER TABLE {table_name} ADD COLUMN {col_name} {col_type_clean}"))
            db_session.commit()
            return True, "added"
        except:
            return False, f"Error: {e}"
    except Exception as e:
        return False, f"Error: {e}"

with app.app_context():
    print("=" * 70)
    print("ULTIMATE DATABASE SCHEMA FIX")
    print("=" * 70)
    print()
    
    inspector = inspect(db.engine)
    all_tables = inspector.get_table_names()
    print(f"Found {len(all_tables)} tables in database")
    print()
    
    fixes_applied = 0
    
    # Fix InventoryItem - CRITICAL
    print("=" * 70)
    print("FIXING InventoryItem table (CRITICAL)...")
    print("=" * 70)
    if "inventory_item" in all_tables:
        existing = get_table_columns(inspector, "inventory_item")
        print(f"Current columns: {', '.join(existing)}")
        print()
        
        inventory_fixes = [
            ("description", "TEXT"),
            ("unit_price_ugx", "NUMERIC(12,2) DEFAULT 0.00"),
            ("category", "VARCHAR(100)"),
            ("sku", "VARCHAR(100)"),
            ("replacement_cost", "NUMERIC(10,2)"),
            ("condition", "VARCHAR(50)"),
            ("location", "VARCHAR(100)"),
            ("tags", "VARCHAR(255)"),
            ("status", "VARCHAR(50)"),
            ("created_at", "DATETIME"),
            ("updated_at", "DATETIME"),
        ]
        
        for col_name, col_type in inventory_fixes:
            success, message = add_column_safe("inventory_item", col_name, col_type, inspector, db.session)
            if success:
                print(f"  ✓ ADDED 'inventory_item.{col_name}'")
                fixes_applied += 1
            elif message == "exists":
                print(f"  ✓ 'inventory_item.{col_name}' already exists")
            else:
                print(f"  ⚠ 'inventory_item.{col_name}': {message}")
    else:
        print("  ⚠ inventory_item table does not exist")
    
    print()
    
    # Fix IncomingLead
    print("=" * 70)
    print("FIXING IncomingLead table...")
    print("=" * 70)
    if "incoming_lead" in all_tables:
        existing = get_table_columns(inspector, "incoming_lead")
        print(f"Current columns: {', '.join(existing)}")
        print()
        
        incoming_lead_fixes = [
            ("email", "VARCHAR(120)"),
        ]
        
        for col_name, col_type in incoming_lead_fixes:
            success, message = add_column_safe("incoming_lead", col_name, col_type, inspector, db.session)
            if success:
                print(f"  ✓ ADDED 'incoming_lead.{col_name}'")
                fixes_applied += 1
            elif message == "exists":
                print(f"  ✓ 'incoming_lead.{col_name}' already exists")
    
    print()
    
    # Verify critical queries work
    print("=" * 70)
    print("TESTING CRITICAL QUERIES...")
    print("=" * 70)
    
    try:
        from models import InventoryItem, IncomingLead
        
        # Test InventoryItem query
        try:
            count = InventoryItem.query.filter(InventoryItem.stock_count <= 10).count()
            print(f"✓ InventoryItem query works: {count} items with low stock")
        except Exception as e:
            print(f"✗ InventoryItem query FAILED: {e}")
        
        # Test IncomingLead query
        try:
            count = IncomingLead.query.filter_by(pipeline_stage='New Lead').count()
            print(f"✓ IncomingLead query works: {count} new leads")
        except Exception as e:
            print(f"✗ IncomingLead query FAILED: {e}")
            
    except Exception as e:
        print(f"✗ Error testing queries: {e}")
        import traceback
        traceback.print_exc()
    
    print()
    print("=" * 70)
    print(f"✅ SCHEMA FIX COMPLETED! Applied {fixes_applied} fix(es).")
    print("=" * 70)
    print()
    print("⚠️  IMPORTANT: Restart your Flask application NOW!")
    print("   The database schema has been updated and the app needs to reconnect.")

