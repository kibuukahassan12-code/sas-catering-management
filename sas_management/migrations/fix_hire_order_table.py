"""Migration script to add missing columns to hire_order table."""
from sas_management.models import db
from sqlalchemy import inspect, text


def fix_hire_order_table():
    """Add missing columns to hire_order table if they don't exist."""
    try:
        inspector = inspect(db.engine)
        
        # Check if table exists
        if "hire_order" not in inspector.get_table_names():
            print("[INFO] hire_order table does not exist. It will be created by db.create_all()")
            return
        
        existing = [col['name'] for col in inspector.get_columns("hire_order")]
        
        required = {
            "event_date": "DATE",
            "start_date": "DATE",
            "end_date": "DATE",
            "delivery_date": "DATE",
            "pickup_date": "DATE",
            "delivery_address": "TEXT",
            "telephone": "TEXT",
            "email": "TEXT",
            "total_cost": "NUMERIC(14,2) DEFAULT 0",
            "amount_paid": "NUMERIC(14,2) DEFAULT 0",
            "balance_due": "NUMERIC(14,2) DEFAULT 0",
            "comments": "TEXT",
            "created_at": "DATETIME",
            "updated_at": "DATETIME"
        }
        
        for col, col_type in required.items():
            if col not in existing:
                try:
                    db.session.execute(text(f"ALTER TABLE hire_order ADD COLUMN {col} {col_type}"))
                    db.session.commit()
                    print(f"[OK] Added column: {col}")
                except Exception as e:
                    error_msg = str(e).lower()
                    if "duplicate column" in error_msg or "already exists" in error_msg:
                        print(f"[INFO] Column {col} already exists (skipping)")
                        db.session.rollback()
                    else:
                        print(f"[ERROR] Failed to add {col}: {e}")
                        db.session.rollback()
            else:
                print(f"[INFO] Column {col} already exists")
    except Exception as e:
        print(f"[ERROR] Migration error: {e}")
        db.session.rollback()

