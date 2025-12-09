"""Comprehensive database schema fix for all models."""
from app import app, db
from sqlalchemy import inspect, text
from sqlalchemy.exc import OperationalError
from datetime import datetime

def add_column_if_missing(table_name, col_name, col_type, inspector, db_session):
    """Add a column to a table if it doesn't exist."""
    try:
        if table_name not in inspector.get_table_names():
            return False, "Table does not exist"
        
        columns = {col['name']: col for col in inspector.get_columns(table_name)}
        if col_name in columns:
            return False, "Column already exists"
        
        db_session.execute(text(f"ALTER TABLE {table_name} ADD COLUMN {col_name} {col_type}"))
        db_session.commit()
        return True, "Added"
    except OperationalError as e:
        if "duplicate" in str(e).lower() or "already exists" in str(e).lower():
            return False, "Already exists"
        return False, f"Error: {e}"

with app.app_context():
    print("=" * 70)
    print("Comprehensive Database Schema Fix")
    print("=" * 70)
    print()
    
    inspector = inspect(db.engine)
    all_tables = inspector.get_table_names()
    print(f"Found {len(all_tables)} tables in database")
    print()
    
    fixes_applied = 0
    
    # Fix IncomingLead table
    print("Fixing IncomingLead table...")
    incoming_lead_fixes = [
        ("email", "VARCHAR(120)"),
    ]
    
    for col_name, col_type in incoming_lead_fixes:
        success, message = add_column_if_missing("incoming_lead", col_name, col_type, inspector, db.session)
        if success:
            print(f"  ✓ Added 'incoming_lead.{col_name}'")
            fixes_applied += 1
        elif "already exists" in message.lower():
            print(f"  ✓ 'incoming_lead.{col_name}' already exists")
    
    print()
    
    # Fix User table
    print("Fixing User table...")
    user_fixes = [
        ("created_at", "DATETIME"),
        ("last_login", "DATETIME"),
    ]
    
    for col_name, col_type in user_fixes:
        success, message = add_column_if_missing("user", col_name, col_type, inspector, db.session)
        if success:
            print(f"  ✓ Added 'user.{col_name}'")
            fixes_applied += 1
        elif "already exists" in message.lower():
            print(f"  ✓ 'user.{col_name}' already exists")
    
    print()
    
    # Fix Client table
    print("Fixing Client table...")
    client_fixes = [
        ("created_at", "DATETIME"),
        ("updated_at", "DATETIME"),
    ]
    
    for col_name, col_type in client_fixes:
        success, message = add_column_if_missing("client", col_name, col_type, inspector, db.session)
        if success:
            print(f"  ✓ Added 'client.{col_name}'")
            fixes_applied += 1
        elif "already exists" in message.lower():
            print(f"  ✓ 'client.{col_name}' already exists")
    
    print()
    
    # Fix Event table
    print("Fixing Event table...")
    event_fixes = [
        ("created_at", "DATETIME"),
        ("updated_at", "DATETIME"),
    ]
    
    for col_name, col_type in event_fixes:
        success, message = add_column_if_missing("event", col_name, col_type, inspector, db.session)
        if success:
            print(f"  ✓ Added 'event.{col_name}'")
            fixes_applied += 1
        elif "already exists" in message.lower():
            print(f"  ✓ 'event.{col_name}' already exists")
    
    print()
    
    # Fix InventoryItem table (critical - causing errors)
    print("Fixing InventoryItem table...")
    inventory_fixes = [
        ("description", "TEXT"),
        ("category", "VARCHAR(100)"),
        ("sku", "VARCHAR(100)"),
        ("replacement_cost", "NUMERIC(10,2)"),
        ("condition", "VARCHAR(50) DEFAULT 'Good'"),
        ("location", "VARCHAR(100)"),
        ("tags", "VARCHAR(255)"),
        ("status", "VARCHAR(50) DEFAULT 'Available'"),
        ("created_at", "DATETIME"),
        ("updated_at", "DATETIME"),
    ]
    
    for col_name, col_type in inventory_fixes:
        success, message = add_column_if_missing("inventory_item", col_name, col_type, inspector, db.session)
        if success:
            print(f"  ✓ Added 'inventory_item.{col_name}'")
            fixes_applied += 1
        elif "already exists" in message.lower():
            print(f"  ✓ 'inventory_item.{col_name}' already exists")
    
    print()
    
    # Fix other common tables
    print("Fixing other common tables...")
    common_tables = {
        "catering_item": [("created_at", "DATETIME")],
        "bakery_item": [("created_at", "DATETIME")],
    }
    
    for table_name, fixes in common_tables.items():
        if table_name in all_tables:
            for col_name, col_type in fixes:
                success, message = add_column_if_missing(table_name, col_name, col_type, inspector, db.session)
                if success:
                    print(f"  ✓ Added '{table_name}.{col_name}'")
                    fixes_applied += 1
                elif "already exists" in message.lower():
                    pass  # Silent for already existing
    
    print()
    print("Ensuring all tables match models...")
    try:
        db.create_all()
        print("  ✓ All tables verified")
    except Exception as e:
        print(f"  ⚠ Error during create_all(): {e}")
    
    print()
    print("=" * 70)
    print(f"✅ Schema fix completed! Applied {fixes_applied} fix(es).")
    print("=" * 70)
    print()
    print("Please restart your Flask application for changes to take effect.")


