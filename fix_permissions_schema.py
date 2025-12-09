"""
Fix permissions table schema - Add missing 'code' column if it doesn't exist.
This is a safe fallback script if migrations fail.
"""
from app import create_app, db
from models import Permission
from sqlalchemy import inspect, text

app = create_app()

with app.app_context():
    print("="*60)
    print("FIXING PERMISSIONS TABLE SCHEMA")
    print("="*60)
    
    try:
        # Check if permissions table exists
        inspector = inspect(db.engine)
        table_names = inspector.get_table_names()
        
        if "permissions" not in table_names:
            print("⚠️ Permissions table does not exist. Creating it...")
            db.create_all()
            print("✅ Permissions table created")
        else:
            print("✓ Permissions table exists")
            
            # Check columns in permissions table
            columns = [col['name'] for col in inspector.get_columns("permissions")]
            print(f"\nCurrent columns: {', '.join(columns)}")
            
            # Check if 'code' column exists
            if "code" not in columns:
                print("\n⚠️ Column 'code' missing — adding it now...")
                try:
                    # Try to add the column
                    db.session.execute(text("ALTER TABLE permissions ADD COLUMN code VARCHAR(100)"))
                    db.session.commit()
                    print("✅ Column 'code' added successfully")
                except Exception as e:
                    print(f"❌ Error adding column: {e}")
                    print("Attempting to recreate table...")
                    db.session.rollback()
                    
                    # Backup existing data if any
                    try:
                        existing_perms = db.session.execute(text("SELECT * FROM permissions")).fetchall()
                        if existing_perms:
                            print(f"⚠️ Found {len(existing_perms)} existing permissions - backing up...")
                    except:
                        pass
                    
                    # Drop and recreate
                    try:
                        db.session.execute(text("DROP TABLE IF EXISTS permissions"))
                        db.session.commit()
                        db.create_all()
                        print("✅ Permissions table recreated with correct schema")
                    except Exception as e2:
                        print(f"❌ Error recreating table: {e2}")
                        db.session.rollback()
            else:
                print("✓ Column 'code' already exists")
            
            # Verify final schema
            print("\n" + "="*60)
            print("FINAL SCHEMA VERIFICATION")
            print("="*60)
            final_columns = [col['name'] for col in inspector.get_columns("permissions")]
            print(f"Columns: {', '.join(final_columns)}")
            
            required_columns = ['id', 'code', 'name', 'group', 'description']
            missing = [col for col in required_columns if col not in final_columns]
            
            if missing:
                print(f"⚠️ Missing columns: {', '.join(missing)}")
            else:
                print("✅ All required columns present!")
                
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        db.session.rollback()

    print("\n" + "="*60)
    print("SCHEMA FIX COMPLETE")
    print("="*60)

