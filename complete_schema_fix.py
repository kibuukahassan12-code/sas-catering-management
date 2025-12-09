"""
Complete schema fix - add all missing columns to permissions table.
"""
from app import create_app, db
from sqlalchemy import inspect, text

app = create_app()

with app.app_context():
    print("="*60)
    print("COMPLETE PERMISSIONS SCHEMA FIX")
    print("="*60)
    
    try:
        inspector = inspect(db.engine)
        columns = [col['name'] for col in inspector.get_columns("permissions")]
        print(f"\nCurrent columns: {', '.join(columns)}")
        
        # Add missing columns
        if 'group' not in columns:
            print("\nAdding 'group' column...")
            try:
                # 'group' is a reserved keyword, need to escape it
                db.session.execute(text('ALTER TABLE permissions ADD COLUMN "group" VARCHAR(100)'))
                db.session.commit()
                print("✅ Column 'group' added")
            except Exception as e:
                print(f"⚠️  Error adding 'group': {e}")
                db.session.rollback()
        
        if 'description' not in columns:
            print("Adding 'description' column...")
            try:
                db.session.execute(text("ALTER TABLE permissions ADD COLUMN description VARCHAR(300)"))
                db.session.commit()
                print("✅ Column 'description' added")
            except Exception as e:
                print(f"⚠️  Error adding 'description': {e}")
                db.session.rollback()
        
        # Verify final state
        print("\n" + "="*60)
        print("FINAL VERIFICATION")
        print("="*60)
        final_columns = [col['name'] for col in inspector.get_columns("permissions")]
        print(f"Final columns: {', '.join(final_columns)}")
        
        required = ['id', 'code', 'name', 'group', 'description']
        missing = [col for col in required if col not in final_columns]
        
        if missing:
            print(f"⚠️  Still missing: {', '.join(missing)}")
        else:
            print("✅ All required columns present!")
            
            # Try to populate code column from module/action if they exist
            if 'module' in final_columns and 'action' in final_columns:
                print("\nMigrating data from module/action to code...")
                try:
                    perms = db.session.execute(text("SELECT id, module, action FROM permissions WHERE code IS NULL OR code = ''")).fetchall()
                    if perms:
                        print(f"Found {len(perms)} permissions to migrate...")
                        for perm_id, module, action in perms:
                            code = f"{module}.{action}" if module and action else (action if action else "unknown")
                            group_val = module if module else "general"
                            db.session.execute(
                                text('UPDATE permissions SET code = :code, "group" = :group WHERE id = :id'),
                                {"code": code, "group": group_val, "id": perm_id}
                            )
                        db.session.commit()
                        print(f"✅ Migrated {len(perms)} permissions")
                    else:
                        print("✓ No permissions need migration")
                except Exception as e:
                    print(f"⚠️  Migration error: {e}")
                    db.session.rollback()
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        db.session.rollback()
    
    print("\n" + "="*60)
    print("SCHEMA FIX COMPLETE")
    print("="*60)

