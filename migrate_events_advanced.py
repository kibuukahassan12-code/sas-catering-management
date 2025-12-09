"""Migration script to add advanced event fields and new event-related tables."""
from app import app, db
from sqlalchemy.exc import OperationalError
from sqlalchemy import text

with app.app_context():
    print("Starting Events Advanced migration...")
    
    try:
        # Add new columns to Event table
        new_columns = [
            ("event_type", "VARCHAR(100)"),
            ("event_time", "VARCHAR(50)"),
            ("venue", "VARCHAR(255)"),
            ("venue_map_link", "VARCHAR(500)"),
            ("cover_photo", "VARCHAR(500)"),
            ("notes", "TEXT"),
            ("created_at", "DATETIME"),
            ("updated_at", "DATETIME")
        ]
        
        for col_name, col_type in new_columns:
            try:
                db.session.execute(text(f"ALTER TABLE event ADD COLUMN {col_name} {col_type}"))
                db.session.commit()
                print(f"✓ Added column '{col_name}' to Event table.")
            except OperationalError as e:
                if "duplicate column name" in str(e).lower():
                    print(f"  Column '{col_name}' already exists. Skipping.")
                else:
                    raise e
        
        # Create all new tables
        db.create_all()
        print("✓ Created all new event-related tables (EventStaffAssignment, EventMenuSelection, EventDocument, EventCommunication).")
        
        print("\n✅ Events Advanced migration completed successfully!")
        
    except Exception as e:
        print(f"\n❌ Migration error: {str(e)}")
        db.session.rollback()
        raise e

exit()

