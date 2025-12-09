"""
Complete fix for permissions table - migrate from old schema (module/action) to new schema (code/group).
"""
from app import create_app, db
from models import Permission
from sqlalchemy import inspect, text

app = create_app()

with app.app_context():
    print("="*60)
    print("COMPLETE PERMISSIONS TABLE MIGRATION")
    print("="*60)
    
    try:
        inspector = inspect(db.engine)
        
        # Check current columns
        columns = [col['name'] for col in inspector.get_columns("permissions")]
        print(f"\nCurrent columns: {', '.join(columns)}")
        
        # Check if we have old schema (module/action) or new schema (code/group)
        has_old_schema = 'module' in columns or 'action' in columns
        has_new_schema = 'code' in columns and 'group' in columns
        
        if has_old_schema and not has_new_schema:
            print("\n⚠️ Detected old schema (module/action) - migrating to new schema (code/group)...")
            
            # Backup existing data
            try:
                existing_data = db.session.execute(text("SELECT id, name, module, action FROM permissions")).fetchall()
                print(f"Found {len(existing_data)} existing permissions to migrate")
            except Exception as e:
                print(f"Could not read existing data: {e}")
                existing_data = []
            
            # Add new columns if they don't exist
            if 'code' not in columns:
                print("Adding 'code' column...")
                db.session.execute(text("ALTER TABLE permissions ADD COLUMN code VARCHAR(100)"))
            
            if 'group' not in columns:
                print("Adding 'group' column...")
                db.session.execute(text("ALTER TABLE permissions ADD COLUMN group VARCHAR(100)"))
            
            if 'description' not in columns:
                print("Adding 'description' column...")
                db.session.execute(text("ALTER TABLE permissions ADD COLUMN description VARCHAR(300)"))
            
            db.session.commit()
            print("✅ New columns added")
            
            # Migrate data from old schema to new schema
            if existing_data:
                print("\nMigrating data...")
                for perm_id, name, module, action in existing_data:
                    # Create code from module.action format
                    code = f"{module}.{action}" if module and action else f"{action}" if action else "unknown"
                    # Use module as group
                    group = module if module else "general"
                    # Use name or create from module/action
                    perm_name = name if name else f"{module} {action}".title() if module and action else action.title() if action else "Unknown"
                    
                    try:
                        db.session.execute(
                            text("UPDATE permissions SET code = :code, group = :group, name = :name WHERE id = :id"),
                            {"code": code, "group": group, "name": perm_name, "id": perm_id}
                        )
                        print(f"  ✓ Migrated permission {perm_id}: {code}")
                    except Exception as e:
                        print(f"  ✗ Error migrating permission {perm_id}: {e}")
                
                db.session.commit()
                print("✅ Data migration complete")
            
        elif has_new_schema:
            print("\n✓ Already using new schema (code/group)")
        else:
            print("\n⚠️ Unknown schema - creating fresh table...")
            db.create_all()
        
        # Final verification
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
            
        # Show sample data
        try:
            sample = db.session.execute(text("SELECT id, code, name, group FROM permissions LIMIT 5")).fetchall()
            if sample:
                print(f"\nSample permissions ({len(sample)} shown):")
                for perm in sample:
                    print(f"  - {perm[1]} ({perm[2]}) in group '{perm[3]}'")
        except Exception as e:
            print(f"\nCould not read sample data: {e}")
                
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        db.session.rollback()

    print("\n" + "="*60)
    print("MIGRATION COMPLETE")
    print("="*60)

