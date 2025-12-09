"""Fix transaction table - 'transaction' is a reserved keyword in SQLite."""
from app import app, db
from sqlalchemy import inspect, text

with app.app_context():
    inspector = inspect(db.engine)
    
    # Check if transaction table exists
    if "transaction" in inspector.get_table_names():
        existing = [col['name'] for col in inspector.get_columns("transaction")]
        print(f"Transaction table columns: {', '.join(existing)}")
        
        if "created_at" not in existing:
            try:
                # Use brackets to escape the reserved keyword
                db.session.execute(text('ALTER TABLE "transaction" ADD COLUMN created_at DATETIME'))
                db.session.commit()
                print("✓ Added created_at to transaction table")
            except Exception as e:
                print(f"✗ Error: {e}")
        else:
            print("✓ created_at already exists in transaction table")
    else:
        print("⚠ transaction table does not exist")

