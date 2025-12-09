"""
Check and fix database migrations for RBAC upgrade.
"""
from app import create_app, db
from sqlalchemy import inspect, text

app = create_app()

with app.app_context():
    print("="*60)
    print("DATABASE MIGRATION CHECK")
    print("="*60)
    
    inspector = inspect(db.engine)
    
    # Check permissions table
    print("\n1. Checking permissions table...")
    if "permissions" in inspector.get_table_names():
        perm_columns = [col['name'] for col in inspector.get_columns("permissions")]
        print(f"   Columns: {', '.join(perm_columns)}")
        
        required_perm_cols = ['id', 'code', 'name', 'group', 'description']
        missing_perm = [c for c in required_perm_cols if c not in perm_columns]
        
        if missing_perm:
            print(f"   ⚠️  Missing columns: {', '.join(missing_perm)}")
        else:
            print("   ✅ All required columns present")
    else:
        print("   ❌ Permissions table does not exist")
    
    # Check user table
    print("\n2. Checking user table...")
    if "user" in inspector.get_table_names():
        user_columns = [col['name'] for col in inspector.get_columns("user")]
        print(f"   Columns: {', '.join(user_columns)}")
        
        if 'must_change_password' not in user_columns:
            print("   ⚠️  Missing 'must_change_password' column - adding it...")
            try:
                db.session.execute(text("ALTER TABLE user ADD COLUMN must_change_password BOOLEAN DEFAULT 0"))
                db.session.commit()
                print("   ✅ Column added successfully")
            except Exception as e:
                print(f"   ❌ Error: {e}")
                db.session.rollback()
        else:
            print("   ✅ 'must_change_password' column exists")
    else:
        print("   ❌ User table does not exist")
    
    # Check user_roles table
    print("\n3. Checking user_roles table...")
    if "user_roles" in inspector.get_table_names():
        print("   ✅ user_roles table exists (many-to-many relationship)")
    else:
        print("   ⚠️  user_roles table does not exist - will be created on next db.create_all()")
    
    # Check role_permissions table
    print("\n4. Checking role_permissions table...")
    if "role_permissions" in inspector.get_table_names():
        print("   ✅ role_permissions table exists")
    else:
        print("   ⚠️  role_permissions table does not exist - will be created on next db.create_all()")
    
    print("\n" + "="*60)
    print("MIGRATION CHECK COMPLETE")
    print("="*60)

