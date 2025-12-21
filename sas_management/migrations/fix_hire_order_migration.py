"""Migration script to fix hire_order table missing columns."""
from sqlalchemy import inspect, text


def fix_hire_order_table(db):
    """
    Add missing columns to hire_order table if they don't exist.
    
    Args:
        db: SQLAlchemy database instance
    """
    try:
        inspector = inspect(db.engine)
        
        # Check if table exists
        if "hire_order" not in inspector.get_table_names():
            print("[WARNING] hire_order table does not exist. It will be created by db.create_all()")
            return
        
        columns = [col['name'] for col in inspector.get_columns("hire_order")]
        
        required = [
            "event_date", "start_date", "end_date", "delivery_date", "pickup_date",
            "delivery_address", "total_cost", "amount_paid", "balance_due",
            "comments", "created_at", "updated_at"
        ]
        
        missing = [c for c in required if c not in columns]
        
        if not missing:
            print("[OK] All required columns exist in hire_order table")
            return
        
        print(f"Found {len(missing)} missing columns: {', '.join(missing)}")
        
        for col in missing:
            try:
                if col in ["event_date", "start_date", "end_date", "delivery_date", "pickup_date"]:
                    db.session.execute(text(f"ALTER TABLE hire_order ADD COLUMN {col} DATE"))
                elif col in ["created_at", "updated_at"]:
                    db.session.execute(text(f"ALTER TABLE hire_order ADD COLUMN {col} DATETIME"))
                elif col in ["total_cost", "amount_paid", "balance_due"]:
                    db.session.execute(text(f"ALTER TABLE hire_order ADD COLUMN {col} NUMERIC(14,2) DEFAULT 0"))
                elif col == "delivery_address":
                    db.session.execute(text(f"ALTER TABLE hire_order ADD COLUMN {col} TEXT"))
                elif col == "comments":
                    db.session.execute(text(f"ALTER TABLE hire_order ADD COLUMN {col} TEXT"))
                else:
                    db.session.execute(text(f"ALTER TABLE hire_order ADD COLUMN {col} TEXT"))
                
                db.session.commit()
                print(f"[OK] Added missing column: {col}")
            except Exception as e:
                error_msg = str(e).lower()
                if "duplicate column" in error_msg or "already exists" in error_msg:
                    print(f"[WARNING] Column {col} already exists (skipping)")
                    db.session.rollback()
                else:
                    print(f"[ERROR] Failed to add column {col}: {e}")
                    db.session.rollback()
        
        print("[OK] Migration completed")
    except Exception as e:
        print(f"[ERROR] Migration error: {e}")
        db.session.rollback()

