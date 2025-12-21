# Safe DB patch: adds missing columns to service_events and ensures supporting tables exist.
import sqlite3, os, sys
DB_CANDIDATES = [
    os.path.join("sas_management","database","sas.db"),
    os.path.join("sas_management","sas.db"),
    "sas.db"
]
DB_PATH = next((p for p in DB_CANDIDATES if os.path.exists(p)), DB_CANDIDATES[0])
print("Using DB:", DB_PATH)
conn = sqlite3.connect(DB_PATH)
c = conn.cursor()
# Check if service_events table exists
c.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='service_events'")
table_exists = c.fetchone() is not None

if table_exists:
    # Ensure columns on service_events
    needed = {
        "event_id":"TEXT",
        "event_type":"TEXT",
        "client_name":"TEXT",
        "notes":"TEXT",
        "status":"TEXT"
    }
    c.execute("PRAGMA table_info(service_events)")
    existing = [r[1] for r in c.fetchall()]
    for col, ctype in needed.items():
        if col not in existing:
            try:
                print(f"[PATCH] Adding column {col}")
                c.execute(f"ALTER TABLE service_events ADD COLUMN {col} {ctype} DEFAULT ''")
            except Exception as e:
                print(f"  [WARN] Could not add {col}: {e}")
else:
    print("[INFO] service_events table does not exist yet - will be created by SQLAlchemy on app startup")
# Create supporting tables if missing
c.execute('''CREATE TABLE IF NOT EXISTS service_event_items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    event_id INTEGER,
    item_name TEXT,
    category TEXT,
    quantity_needed INTEGER DEFAULT 0,
    quantity_assigned INTEGER DEFAULT 0,
    notes TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
)''')
print("[OK] service_event_items ensured")
c.execute('''CREATE TABLE IF NOT EXISTS service_team_assignments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    event_id INTEGER,
    staff_name TEXT,
    staff_role TEXT,
    phone TEXT,
    notes TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
)''')
print("[OK] service_team_assignments ensured")
c.execute('''CREATE TABLE IF NOT EXISTS service_checklist (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    event_id INTEGER,
    task TEXT,
    is_complete INTEGER DEFAULT 0,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
)''')
print("[OK] service_checklist ensured")
conn.commit()
conn.close()
print("DB patch finished.")

