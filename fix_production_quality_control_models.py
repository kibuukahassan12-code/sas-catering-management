"""Fix production quality control models by adding missing columns."""
import sqlite3
import os
import sys

# Add the project root to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import app, db

def fix_production_models():
    """Add missing columns to production quality control tables."""
    with app.app_context():
        try:
            conn = db.engine.raw_connection()
            cursor = conn.cursor()
        except Exception as e:
            print(f"Error connecting to database: {e}")
            return
        
        print("Fixing Production Quality Control Models...")
        
        # Fix KitchenChecklist table
        print("\n1. Fixing KitchenChecklist table...")
        kitchen_columns_to_add = [
            ("checklist_date", "DATE"),
            ("checked_by", "INTEGER"),
            ("status", "VARCHAR(50) DEFAULT 'Pending'"),
            ("notes", "TEXT"),
            ("items", "TEXT"),  # JSON stored as TEXT
            ("completed_at", "DATETIME"),
        ]
        
        for col_name, col_type in kitchen_columns_to_add:
            try:
                cursor.execute(f"PRAGMA table_info(kitchen_checklist)")
                columns = [row[1] for row in cursor.fetchall()]
                if col_name in columns:
                    print(f"  ✓ Column 'kitchen_checklist.{col_name}' already exists")
                else:
                    cursor.execute(f"ALTER TABLE kitchen_checklist ADD COLUMN {col_name} {col_type}")
                    print(f"  ✓ Added column 'kitchen_checklist.{col_name}'")
            except Exception as e:
                print(f"  ✗ Error adding 'kitchen_checklist.{col_name}': {e}")
        
        # Fix DeliveryQCChecklist table
        print("\n2. Fixing DeliveryQCChecklist table...")
        delivery_columns_to_add = [
            ("delivery_date", "DATE"),
            ("delivery_time", "TIME"),
            ("checked_by", "INTEGER"),
            ("temperature_check", "VARCHAR(255)"),
            ("packaging_integrity", "VARCHAR(50) DEFAULT 'Good'"),
            ("presentation", "VARCHAR(50) DEFAULT 'Acceptable'"),
            ("quantity_verified", "BOOLEAN DEFAULT 0"),
            ("customer_satisfaction", "TEXT"),
            ("issues", "TEXT"),
            ("notes", "TEXT"),
        ]
        
        for col_name, col_type in delivery_columns_to_add:
            try:
                cursor.execute(f"PRAGMA table_info(delivery_qc_checklist)")
                columns = [row[1] for row in cursor.fetchall()]
                if col_name in columns:
                    print(f"  ✓ Column 'delivery_qc_checklist.{col_name}' already exists")
                else:
                    cursor.execute(f"ALTER TABLE delivery_qc_checklist ADD COLUMN {col_name} {col_type}")
                    print(f"  ✓ Added column 'delivery_qc_checklist.{col_name}'")
            except Exception as e:
                print(f"  ✗ Error adding 'delivery_qc_checklist.{col_name}': {e}")
        
        # Fix FoodSafetyLog table
        print("\n3. Fixing FoodSafetyLog table...")
        food_safety_columns_to_add = [
            ("log_time", "TIME"),
            ("logged_by", "INTEGER"),
            ("category", "VARCHAR(100)"),
            ("item_description", "TEXT"),
            ("action_taken", "TEXT"),
            ("status", "VARCHAR(50) DEFAULT 'Normal'"),
        ]
        
        for col_name, col_type in food_safety_columns_to_add:
            try:
                cursor.execute(f"PRAGMA table_info(food_safety_log)")
                columns = [row[1] for row in cursor.fetchall()]
                if col_name in columns:
                    print(f"  ✓ Column 'food_safety_log.{col_name}' already exists")
                else:
                    cursor.execute(f"ALTER TABLE food_safety_log ADD COLUMN {col_name} {col_type}")
                    print(f"  ✓ Added column 'food_safety_log.{col_name}'")
            except Exception as e:
                print(f"  ✗ Error adding 'food_safety_log.{col_name}': {e}")
        
        # Fix HygieneReport table
        print("\n4. Fixing HygieneReport table...")
        hygiene_columns_to_add = [
            ("report_time", "TIME"),
            ("event_id", "INTEGER"),
            ("inspected_by", "INTEGER"),
            ("checklist_items", "TEXT"),  # JSON stored as TEXT
            ("overall_rating", "VARCHAR(50) DEFAULT 'Good'"),
            ("issues_found", "TEXT"),
            ("corrective_actions", "TEXT"),
            ("status", "VARCHAR(50) DEFAULT 'Completed'"),
            ("follow_up_date", "DATE"),
        ]
        
        for col_name, col_type in hygiene_columns_to_add:
            try:
                cursor.execute(f"PRAGMA table_info(hygiene_report)")
                columns = [row[1] for row in cursor.fetchall()]
                if col_name in columns:
                    print(f"  ✓ Column 'hygiene_report.{col_name}' already exists")
                else:
                    cursor.execute(f"ALTER TABLE hygiene_report ADD COLUMN {col_name} {col_type}")
                    print(f"  ✓ Added column 'hygiene_report.{col_name}'")
            except Exception as e:
                print(f"  ✗ Error adding 'hygiene_report.{col_name}': {e}")
        
        conn.commit()
        conn.close()
        print("\n✅ Production Quality Control models fixed successfully!")

if __name__ == "__main__":
    fix_production_models()

