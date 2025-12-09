"""Comprehensive database schema fix script using Flask app context."""
from app import app, db
from sqlalchemy import inspect, text
from sqlalchemy.exc import OperationalError
from datetime import datetime

with app.app_context():
    print("=" * 60)
    print("Database Schema Fix Script")
    print("=" * 60)
    print()
    
    inspector = inspect(db.engine)
    
    # Check User table
    print("Checking User table...")
    if "user" in inspector.get_table_names():
        try:
            columns = {col['name']: col for col in inspector.get_columns("user")}
            print(f"  Existing columns: {', '.join(columns.keys())}")
            
            # Check for missing columns
            missing_columns = []
            if "created_at" not in columns:
                missing_columns.append(("created_at", "DATETIME"))
            if "last_login" not in columns:
                missing_columns.append(("last_login", "DATETIME"))
            
            if missing_columns:
                print(f"  Adding {len(missing_columns)} missing column(s)...")
                for col_name, col_type in missing_columns:
                    try:
                        db.session.execute(text(f"ALTER TABLE user ADD COLUMN {col_name} {col_type}"))
                        db.session.commit()
                        print(f"    ✓ Added 'user.{col_name}'")
                    except OperationalError as e:
                        if "duplicate" not in str(e).lower() and "already exists" not in str(e).lower():
                            print(f"    ✗ Error adding 'user.{col_name}': {e}")
                        else:
                            print(f"    ✓ 'user.{col_name}' already exists")
            else:
                print("  ✓ All required columns exist")
                
            # Set default created_at for existing records if needed
            try:
                result = db.session.execute(text("SELECT COUNT(*) FROM user WHERE created_at IS NULL"))
                null_count = result.scalar()
                if null_count > 0:
                    db.session.execute(text("UPDATE user SET created_at = :now WHERE created_at IS NULL"), 
                                     {"now": datetime.utcnow()})
                    db.session.commit()
                    print(f"  ✓ Set default created_at for {null_count} user(s)")
            except Exception as e:
                print(f"  ⚠ Could not update created_at defaults: {e}")
                
        except Exception as e:
            print(f"  ✗ Error checking User table: {e}")
            import traceback
            traceback.print_exc()
    else:
        print("  ⚠ User table does not exist. Creating all tables...")
        db.create_all()
        print("  ✓ Created all tables")
    
    print()
    
    # Check IncomingLead table (critical - causing errors)
    print("Checking IncomingLead table...")
    if "incoming_lead" in inspector.get_table_names():
        try:
            columns = {col['name']: col for col in inspector.get_columns("incoming_lead")}
            print(f"  Existing columns: {', '.join(columns.keys())}")
            
            # Required columns for IncomingLead model
            required_columns = {
                "client_name": "VARCHAR(255) NOT NULL",
                "email": "VARCHAR(120)",
                "phone": "VARCHAR(50)",
                "inquiry_type": "VARCHAR(100)",
                "message": "TEXT",
                "pipeline_stage": "VARCHAR(50) NOT NULL DEFAULT 'New Lead'",
                "assigned_user_id": "INTEGER",
                "converted_client_id": "INTEGER",
                "converted_event_id": "INTEGER",
                "timestamp": "DATETIME NOT NULL",
                "updated_at": "DATETIME NOT NULL"
            }
            
            missing = []
            for col_name, col_def in required_columns.items():
                if col_name not in columns:
                    missing.append((col_name, col_def))
            
            if missing:
                print(f"  Adding {len(missing)} missing column(s)...")
                for col_name, col_def in missing:
                    try:
                        db.session.execute(text(f"ALTER TABLE incoming_lead ADD COLUMN {col_name} {col_def}"))
                        db.session.commit()
                        print(f"    ✓ Added 'incoming_lead.{col_name}'")
                    except OperationalError as e:
                        if "duplicate" not in str(e).lower() and "already exists" not in str(e).lower():
                            print(f"    ✗ Error adding 'incoming_lead.{col_name}': {e}")
                        else:
                            print(f"    ✓ 'incoming_lead.{col_name}' already exists")
            else:
                print("  ✓ All required columns exist")
                
        except Exception as e:
            print(f"  ✗ Error checking IncomingLead table: {e}")
            import traceback
            traceback.print_exc()
    else:
        print("  ⚠ IncomingLead table does not exist. Will be created by db.create_all()")
    
    print()
    
    # Check other common tables for missing columns
    print("Checking other tables for common missing columns...")
    tables_to_check = {
        "client": ["created_at", "updated_at"],
        "event": ["created_at", "updated_at"],
        "catering_item": ["created_at"],
        "bakery_item": ["created_at"],
        "inventory_item": ["created_at", "updated_at"],
    }
    
    for table_name, required_cols in tables_to_check.items():
        if table_name in inspector.get_table_names():
            try:
                columns = {col['name']: col for col in inspector.get_columns(table_name)}
                missing = [col for col in required_cols if col not in columns]
                if missing:
                    for col_name in missing:
                        try:
                            db.session.execute(text(f"ALTER TABLE {table_name} ADD COLUMN {col_name} DATETIME"))
                            db.session.commit()
                            print(f"  ✓ Added '{table_name}.{col_name}'")
                        except OperationalError as e:
                            if "duplicate" not in str(e).lower():
                                print(f"  ⚠ Could not add '{table_name}.{col_name}': {e}")
            except Exception as e:
                print(f"  ⚠ Could not check '{table_name}': {e}")
    
    print()
    print("Ensuring all tables match models...")
    try:
        # This will create any missing tables but won't alter existing ones
        db.create_all()
        print("  ✓ All tables verified")
    except Exception as e:
        print(f"  ⚠ Error during create_all(): {e}")
    
    print()
    print("=" * 60)
    print("✅ Database schema fix completed!")
    print("=" * 60)
    print()
    print("Please restart your Flask application for changes to take effect.")

