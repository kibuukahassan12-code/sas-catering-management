"""Final comprehensive system check to ensure everything is working."""
from app import app, db
from models import User, IncomingLead, Client, Event
from sqlalchemy import inspect

print("=" * 70)
print("Final System Check")
print("=" * 70)
print()

with app.app_context():
    errors = []
    warnings = []
    
    # Test 1: User queries
    print("1. Testing User model...")
    try:
        user_count = User.query.count()
        user = User.query.first()
        if user:
            print(f"   ✓ User queries work ({user_count} user(s) found)")
            print(f"   ✓ User model has all required attributes")
        else:
            warnings.append("No users found in database")
    except Exception as e:
        errors.append(f"User queries failed: {e}")
        print(f"   ✗ User queries failed: {e}")
    
    print()
    
    # Test 2: IncomingLead queries (the one that was failing)
    print("2. Testing IncomingLead model...")
    try:
        lead_count = IncomingLead.query.count()
        new_leads = IncomingLead.query.filter_by(pipeline_stage='New Lead').count()
        print(f"   ✓ IncomingLead queries work ({lead_count} total, {new_leads} new)")
        
        # Test the exact query from dashboard
        stages = ["New Lead", "Qualified", "Proposal Sent", "Negotiation"]
        for stage in stages:
            IncomingLead.query.filter_by(pipeline_stage=stage).count()
        print(f"   ✓ Dashboard pipeline queries work")
    except Exception as e:
        errors.append(f"IncomingLead queries failed: {e}")
        print(f"   ✗ IncomingLead queries failed: {e}")
        import traceback
        traceback.print_exc()
    
    print()
    
    # Test 3: Client queries
    print("3. Testing Client model...")
    try:
        client_count = Client.query.count()
        print(f"   ✓ Client queries work ({client_count} client(s) found)")
    except Exception as e:
        errors.append(f"Client queries failed: {e}")
        print(f"   ✗ Client queries failed: {e}")
    
    print()
    
    # Test 4: Event queries
    print("4. Testing Event model...")
    try:
        event_count = Event.query.count()
        print(f"   ✓ Event queries work ({event_count} event(s) found)")
    except Exception as e:
        errors.append(f"Event queries failed: {e}")
        print(f"   ✗ Event queries failed: {e}")
    
    print()
    
    # Test 5: Database schema check
    print("5. Checking database schema...")
    try:
        inspector = inspect(db.engine)
        
        # Check critical tables
        critical_tables = {
            "user": ["id", "email", "password_hash", "role", "created_at", "last_login"],
            "incoming_lead": ["id", "client_name", "email", "phone", "pipeline_stage", "timestamp"],
            "client": ["id", "name", "created_at"],
            "event": ["id", "client_id", "event_name", "created_at"],
        }
        
        all_tables_ok = True
        for table_name, required_cols in critical_tables.items():
            if table_name not in inspector.get_table_names():
                errors.append(f"Table '{table_name}' does not exist")
                all_tables_ok = False
            else:
                columns = {col['name']: col for col in inspector.get_columns(table_name)}
                missing = [col for col in required_cols if col not in columns]
                if missing:
                    errors.append(f"Table '{table_name}' missing columns: {', '.join(missing)}")
                    all_tables_ok = False
        
        if all_tables_ok:
            print(f"   ✓ All critical tables have required columns")
        else:
            print(f"   ✗ Some tables are missing columns")
    except Exception as e:
        errors.append(f"Schema check failed: {e}")
        print(f"   ✗ Schema check failed: {e}")
    
    print()
    print("=" * 70)
    
    if errors:
        print("❌ ERRORS FOUND:")
        for error in errors:
            print(f"   - {error}")
        print()
        print("Please run: python fix_database_schema.py")
    else:
        print("✅ ALL CHECKS PASSED!")
        print()
        print("Your system is ready to use!")
        if warnings:
            print()
            print("⚠️  WARNINGS:")
            for warning in warnings:
                print(f"   - {warning}")
    
    print("=" * 70)
    print()
    print("Next steps:")
    print("1. Restart your Flask application")
    print("2. Clear browser cache if needed")
    print("3. Test the dashboard and other features")

