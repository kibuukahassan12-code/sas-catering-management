"""Comprehensive database migration script to add all missing columns."""
from app import app, db
from sqlalchemy.exc import OperationalError
from sqlalchemy import text

with app.app_context():
    print("Starting comprehensive database migration...")
    
    try:
        # Add 'company' column to client table if missing
        try:
            db.session.execute(text("ALTER TABLE client ADD COLUMN company VARCHAR"))
            db.session.commit()
            print("✓ Success: 'company' column added to Client table.")
        except OperationalError as e:
            if "duplicate column name" in str(e).lower() or "already exists" in str(e).lower():
                print("✓ 'company' column already exists in Client table.")
            else:
                raise e
        
        # Add 'event_type' column to event table if missing
        try:
            db.session.execute(text("ALTER TABLE event ADD COLUMN event_type VARCHAR"))
            db.session.commit()
            print("✓ Success: 'event_type' column added to Event table.")
        except OperationalError as e:
            if "duplicate column name" in str(e).lower() or "already exists" in str(e).lower():
                print("✓ 'event_type' column already exists in Event table.")
            else:
                raise e
        
        # Add 'actual_cogs_ugx' column to event table if missing
        try:
            db.session.execute(text("ALTER TABLE event ADD COLUMN actual_cogs_ugx FLOAT"))
            db.session.commit()
            print("✓ Success: 'actual_cogs_ugx' column added to Event table.")
        except OperationalError as e:
            if "duplicate column name" in str(e).lower() or "already exists" in str(e).lower():
                print("✓ 'actual_cogs_ugx' column already exists in Event table.")
            else:
                raise e
        
        # Ensure all tables are created from models
        db.create_all()
        print("✓ Database structure initialized. All tables are up to date.")
        
    except Exception as e:
        print(f"✗ Error during migration: {e}")
        db.session.rollback()
        raise

print("\n✓ Database migration complete!")
print("The application is ready to run.")

