"""Migration script to add production quality control tables."""
import sqlite3
import os
from sqlalchemy.exc import OperationalError
from sqlalchemy import text

# Try to use Flask app context if available
try:
    from app import app, db
    USE_FLASK = True
except ImportError:
    USE_FLASK = False

def migrate_production_quality_control():
    """Migrate production quality control tables."""
    if USE_FLASK:
        with app.app_context():
            _migrate_with_flask()
    else:
        _migrate_with_sqlite()

def _migrate_with_flask():
    """Migrate using Flask app context."""
    print("Starting Production Quality Control module migration (Flask)...")
    print("=" * 60)
    
    try:
        # Create kitchen_checklist table
        try:
            db.session.execute(text("""
                CREATE TABLE IF NOT EXISTS kitchen_checklist (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    checklist_date DATE NOT NULL,
                    event_id INTEGER,
                    checked_by INTEGER NOT NULL,
                    items TEXT NOT NULL,
                    status VARCHAR(50) NOT NULL DEFAULT 'Pending',
                    notes TEXT,
                    created_at DATETIME NOT NULL,
                    completed_at DATETIME,
                    FOREIGN KEY (event_id) REFERENCES event(id),
                    FOREIGN KEY (checked_by) REFERENCES user(id)
                )
            """))
            db.session.commit()
            print("✓ Created table 'kitchen_checklist'")
        except OperationalError as e:
            if "already exists" not in str(e).lower():
                print(f"  Error creating 'kitchen_checklist': {e}")
            else:
                print("  Table 'kitchen_checklist' already exists. Skipping.")
            db.session.rollback()
        
        # Create delivery_qc_checklist table
        try:
            db.session.execute(text("""
                CREATE TABLE IF NOT EXISTS delivery_qc_checklist (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    event_id INTEGER NOT NULL,
                    delivery_date DATE NOT NULL,
                    delivery_time TIME,
                    checked_by INTEGER NOT NULL,
                    temperature_check VARCHAR(50),
                    packaging_integrity VARCHAR(50) NOT NULL DEFAULT 'Good',
                    presentation VARCHAR(50) NOT NULL DEFAULT 'Acceptable',
                    quantity_verified BOOLEAN NOT NULL DEFAULT 0,
                    customer_satisfaction VARCHAR(50),
                    issues TEXT,
                    notes TEXT,
                    signature VARCHAR(255),
                    created_at DATETIME NOT NULL,
                    FOREIGN KEY (event_id) REFERENCES event(id),
                    FOREIGN KEY (checked_by) REFERENCES user(id)
                )
            """))
            db.session.commit()
            print("✓ Created table 'delivery_qc_checklist'")
        except OperationalError as e:
            if "already exists" not in str(e).lower():
                print(f"  Error creating 'delivery_qc_checklist': {e}")
            else:
                print("  Table 'delivery_qc_checklist' already exists. Skipping.")
            db.session.rollback()
        
        # Create food_safety_log table
        try:
            db.session.execute(text("""
                CREATE TABLE IF NOT EXISTS food_safety_log (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    log_date DATE NOT NULL,
                    log_time TIME,
                    event_id INTEGER,
                    logged_by INTEGER NOT NULL,
                    category VARCHAR(100) NOT NULL,
                    item_description VARCHAR(255) NOT NULL,
                    temperature NUMERIC(5,2),
                    action_taken TEXT,
                    status VARCHAR(50) NOT NULL DEFAULT 'Normal',
                    notes TEXT,
                    created_at DATETIME NOT NULL,
                    FOREIGN KEY (event_id) REFERENCES event(id),
                    FOREIGN KEY (logged_by) REFERENCES user(id)
                )
            """))
            db.session.commit()
            print("✓ Created table 'food_safety_log'")
        except OperationalError as e:
            if "already exists" not in str(e).lower():
                print(f"  Error creating 'food_safety_log': {e}")
            else:
                print("  Table 'food_safety_log' already exists. Skipping.")
            db.session.rollback()
        
        # Create hygiene_report table
        try:
            db.session.execute(text("""
                CREATE TABLE IF NOT EXISTS hygiene_report (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    report_date DATE NOT NULL,
                    report_time TIME,
                    event_id INTEGER,
                    inspected_by INTEGER NOT NULL,
                    area VARCHAR(100) NOT NULL,
                    checklist_items TEXT NOT NULL,
                    overall_rating VARCHAR(50) NOT NULL DEFAULT 'Good',
                    issues_found TEXT,
                    corrective_actions TEXT,
                    photos VARCHAR(500),
                    status VARCHAR(50) NOT NULL DEFAULT 'Completed',
                    follow_up_date DATE,
                    created_at DATETIME NOT NULL,
                    FOREIGN KEY (event_id) REFERENCES event(id),
                    FOREIGN KEY (inspected_by) REFERENCES user(id)
                )
            """))
            db.session.commit()
            print("✓ Created table 'hygiene_report'")
        except OperationalError as e:
            if "already exists" not in str(e).lower():
                print(f"  Error creating 'hygiene_report': {e}")
            else:
                print("  Table 'hygiene_report' already exists. Skipping.")
            db.session.rollback()
        
        print("\n✅ Production Quality Control migration completed successfully!")
        
    except Exception as e:
        print(f"\n❌ Migration error: {str(e)}")
        db.session.rollback()
        raise e

def _migrate_with_sqlite():
    """Migrate using direct SQLite connection."""
    # Get the database path
    db_path = os.path.join("instance", "site.db")
    if not os.path.exists(db_path):
        db_path = os.path.join("instance", "app.db")
    
    if not os.path.exists(db_path):
        print(f"Database not found at {db_path}.")
        print("Please run the app once to create the database, then run this migration.")
        return
    
    print(f"Connecting to database at {db_path}...")
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    print("Starting Production Quality Control module migration (SQLite)...")
    
    # Create tables
    tables = {
        "kitchen_checklist": """
            CREATE TABLE IF NOT EXISTS kitchen_checklist (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                checklist_date DATE NOT NULL,
                event_id INTEGER,
                checked_by INTEGER NOT NULL,
                items TEXT NOT NULL,
                status VARCHAR(50) NOT NULL DEFAULT 'Pending',
                notes TEXT,
                created_at DATETIME NOT NULL,
                completed_at DATETIME,
                FOREIGN KEY (event_id) REFERENCES event(id),
                FOREIGN KEY (checked_by) REFERENCES user(id)
            )
        """,
        "delivery_qc_checklist": """
            CREATE TABLE IF NOT EXISTS delivery_qc_checklist (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                event_id INTEGER NOT NULL,
                delivery_date DATE NOT NULL,
                delivery_time TIME,
                checked_by INTEGER NOT NULL,
                temperature_check VARCHAR(50),
                packaging_integrity VARCHAR(50) NOT NULL DEFAULT 'Good',
                presentation VARCHAR(50) NOT NULL DEFAULT 'Acceptable',
                quantity_verified BOOLEAN NOT NULL DEFAULT 0,
                customer_satisfaction VARCHAR(50),
                issues TEXT,
                notes TEXT,
                signature VARCHAR(255),
                created_at DATETIME NOT NULL,
                FOREIGN KEY (event_id) REFERENCES event(id),
                FOREIGN KEY (checked_by) REFERENCES user(id)
            )
        """,
        "food_safety_log": """
            CREATE TABLE IF NOT EXISTS food_safety_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                log_date DATE NOT NULL,
                log_time TIME,
                event_id INTEGER,
                logged_by INTEGER NOT NULL,
                category VARCHAR(100) NOT NULL,
                item_description VARCHAR(255) NOT NULL,
                temperature NUMERIC(5,2),
                action_taken TEXT,
                status VARCHAR(50) NOT NULL DEFAULT 'Normal',
                notes TEXT,
                created_at DATETIME NOT NULL,
                FOREIGN KEY (event_id) REFERENCES event(id),
                FOREIGN KEY (logged_by) REFERENCES user(id)
            )
        """,
        "hygiene_report": """
            CREATE TABLE IF NOT EXISTS hygiene_report (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                report_date DATE NOT NULL,
                report_time TIME,
                event_id INTEGER,
                inspected_by INTEGER NOT NULL,
                area VARCHAR(100) NOT NULL,
                checklist_items TEXT NOT NULL,
                overall_rating VARCHAR(50) NOT NULL DEFAULT 'Good',
                issues_found TEXT,
                corrective_actions TEXT,
                photos VARCHAR(500),
                status VARCHAR(50) NOT NULL DEFAULT 'Completed',
                follow_up_date DATE,
                created_at DATETIME NOT NULL,
                FOREIGN KEY (event_id) REFERENCES event(id),
                FOREIGN KEY (inspected_by) REFERENCES user(id)
            )
        """
    }
    
    for table_name, create_sql in tables.items():
        try:
            cursor.execute(create_sql)
            conn.commit()
            print(f"[OK] Created table '{table_name}'")
        except Exception as e:
            print(f"  Error creating '{table_name}': {e}")
            conn.rollback()
    
    conn.close()
    print("\n✅ Production Quality Control migration completed successfully!")

if __name__ == "__main__":
    migrate_production_quality_control()




