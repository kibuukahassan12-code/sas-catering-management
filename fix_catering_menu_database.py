"""Fix catering menu database by adding missing columns."""
import sqlite3
import os
import sys

# Add the project root to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import app, db

def fix_catering_menu():
    """Add missing columns to catering_item table."""
    with app.app_context():
        try:
            conn = db.engine.raw_connection()
            cursor = conn.cursor()
            
            print("Fixing Catering Menu Database...")
            
            # Add missing columns to catering_item table
            print("\n1. Fixing CateringItem table...")
            columns_to_add = [
                ("selling_price_ugx", "NUMERIC(12, 2)"),
                ("estimated_cogs_ugx", "NUMERIC(12, 2)"),
                ("updated_at", "DATETIME"),
            ]
            
            for col_name, col_type in columns_to_add:
                try:
                    cursor.execute("PRAGMA table_info(catering_item)")
                    columns = [row[1] for row in cursor.fetchall()]
                    if col_name in columns:
                        print(f"  ✓ Column 'catering_item.{col_name}' already exists")
                    else:
                        cursor.execute(f"ALTER TABLE catering_item ADD COLUMN {col_name} {col_type}")
                        print(f"  ✓ Added column 'catering_item.{col_name}'")
                except Exception as e:
                    print(f"  ✗ Error adding 'catering_item.{col_name}': {e}")
            
            # Migrate existing price_ugx to selling_price_ugx if needed
            try:
                cursor.execute("UPDATE catering_item SET selling_price_ugx = price_ugx WHERE selling_price_ugx IS NULL AND price_ugx IS NOT NULL")
                updated = cursor.rowcount
                if updated > 0:
                    print(f"  ✓ Migrated {updated} existing prices to selling_price_ugx")
            except Exception as e:
                print(f"  ⚠ Could not migrate prices: {e}")
            
            conn.commit()
            conn.close()
            print("\n✅ Catering menu database fixed successfully!")
            
        except Exception as e:
            print(f"\n✗ Error fixing catering menu database: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    fix_catering_menu()

