"""
Verify all fixes are applied correctly.
"""
from app import create_app, db
from models import Permission
from sqlalchemy import inspect, text

app = create_app()

with app.app_context():
    print("="*60)
    print("VERIFYING ALL FIXES")
    print("="*60)
    
    # Check 1: Permission model has code column
    print("\n1. Checking Permission model...")
    perm_columns = [col.name for col in Permission.__table__.columns]
    required_cols = ['id', 'code', 'name', 'group', 'description']
    missing_model_cols = [col for col in required_cols if col not in perm_columns]
    
    if missing_model_cols:
        print(f"   ❌ Missing in model: {missing_model_cols}")
    else:
        print(f"   ✅ Model has all required columns: {', '.join(required_cols)}")
    
    # Check 2: Database table has code column
    print("\n2. Checking database table...")
    try:
        inspector = inspect(db.engine)
        db_columns = [col['name'] for col in inspector.get_columns("permissions")]
        missing_db_cols = [col for col in required_cols if col not in db_columns]
        
        if missing_db_cols:
            print(f"   ❌ Missing in database: {missing_db_cols}")
            print(f"   Current columns: {', '.join(db_columns)}")
        else:
            print(f"   ✅ Database has all required columns")
    except Exception as e:
        print(f"   ❌ Error checking database: {e}")
    
    # Check 3: Admin blueprint has request import
    print("\n3. Checking admin blueprint imports...")
    try:
        with open('blueprints/admin/__init__.py', 'r') as f:
            content = f.read()
            if 'from flask import' in content and 'request' in content:
                if 'request' in content.split('from flask import')[1].split('\n')[0]:
                    print("   ✅ 'request' is imported in admin blueprint")
                else:
                    print("   ⚠️  'request' might not be in Flask import")
            else:
                print("   ❌ Could not verify request import")
    except Exception as e:
        print(f"   ❌ Error checking imports: {e}")
    
    # Check 4: Activity logging has request import
    print("\n4. Checking activity logging in app.py...")
    try:
        with open('app.py', 'r') as f:
            content = f.read()
            if 'def log_user_actions():' in content:
                # Check if request is imported in the function
                func_start = content.find('def log_user_actions():')
                func_content = content[func_start:func_start+500]
                if 'from flask import request' in func_content or 'request' in func_content.split('from flask import')[1] if 'from flask import' in func_content else '':
                    print("   ✅ 'request' is imported in log_user_actions function")
                else:
                    print("   ⚠️  Need to verify request import in log_user_actions")
            else:
                print("   ❌ log_user_actions function not found")
    except Exception as e:
        print(f"   ❌ Error checking app.py: {e}")
    
    print("\n" + "="*60)
    print("VERIFICATION COMPLETE")
    print("="*60)
    print("\nIf all checks pass, restart the Flask server to apply changes.")

