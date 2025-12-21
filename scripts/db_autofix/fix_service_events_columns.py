import sqlite3
import os

DB_PATH = "sas_management/instance/sas.db"  # Database path relative to workspace root

COLUMNS_TO_ADD = {
    "client_name": "TEXT",
    "notes": "TEXT"
}

def add_missing_columns():
    if not os.path.exists(DB_PATH):
        print(f"Database not found: {DB_PATH}")
        return

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Check if table exists
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='service_events'")
    if not cursor.fetchone():
        print(f"[ERROR] Table 'service_events' does not exist in the database.")
        print("Please ensure the table is created first (run the Flask app or migrations).")
        conn.close()
        return

    cursor.execute("PRAGMA table_info(service_events)")
    existing_cols = [col[1] for col in cursor.fetchall()]

    for col, col_type in COLUMNS_TO_ADD.items():
        if col not in existing_cols:
            print(f"[FIX] Adding missing column: {col}")
            cursor.execute(
                f"ALTER TABLE service_events ADD COLUMN {col} {col_type} DEFAULT ''"
            )
        else:
            print(f"[OK] Column already exists: {col}")

    conn.commit()
    conn.close()
    print("DONE: service_events table schema corrected.")
    
if __name__ == "__main__":
    add_missing_columns()

