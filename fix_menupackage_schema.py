"""
Fix MenuPackage database schema - Add missing columns safely
"""
from app import app, db
from sqlalchemy import inspect, text

def check_and_fix_menupackage_schema():
    """Check and fix MenuPackage table schema."""
    with app.app_context():
        inspector = inspect(db.engine)
        
        # Check if table exists
        if 'menu_package' not in inspector.get_table_names():
            print("⚠️  menu_package table does not exist. Creating...")
            db.create_all()
            print("✅ Table created.")
            return
        
        # Get existing columns
        columns = {col['name']: col for col in inspector.get_columns('menu_package')}
        print(f"📋 Current columns: {list(columns.keys())}")
        
        # Required columns
        required_columns = {
            'price_per_guest': 'FLOAT',
            'description': 'TEXT',
            'items': 'JSON',
            'created_at': 'DATETIME',
            'updated_at': 'DATETIME'
        }
        
        # Check and add missing columns
        for col_name, col_type in required_columns.items():
            if col_name not in columns:
                try:
                    print(f"➕ Adding column: {col_name} ({col_type})")
                    db.session.execute(text(f"ALTER TABLE menu_package ADD COLUMN {col_name} {col_type}"))
                    db.session.commit()
                    print(f"✅ Added {col_name}")
                except Exception as e:
                    if "duplicate column" in str(e).lower():
                        print(f"  ⚠️  Column {col_name} already exists (ignoring)")
                    else:
                        print(f"  ❌ Error adding {col_name}: {e}")
                        db.session.rollback()
            else:
                print(f"  ✓ Column {col_name} exists")
        
        # Verify final state
        columns_after = {col['name']: col for col in inspector.get_columns('menu_package')}
        print(f"\n✅ Final columns: {list(columns_after.keys())}")
        
        # Check for any issues
        missing = [col for col in required_columns.keys() if col not in columns_after]
        if missing:
            print(f"⚠️  Still missing: {missing}")
        else:
            print("\n🎉 All required columns are present!")

if __name__ == "__main__":
    print("=" * 60)
    print("MenuPackage Schema Fix")
    print("=" * 60)
    check_and_fix_menupackage_schema()
    print("=" * 60)

