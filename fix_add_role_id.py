"""
Migration script to add role_id column to user table if it doesn't exist.
SQLite safe - checks before adding column.
"""
import sqlite3
import os

# Get the database path
db_path = os.path.join("instance", "site.db")
if not os.path.exists(db_path):
    print(f"⚠️  Database not found at {db_path}")
    print("Please run the app once to create the database, then run this script.")
    exit(1)

print(f"Connecting to database at {db_path}...")
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

print("Checking user table structure...")

# Get current columns
cursor.execute("PRAGMA table_info(user)")
columns = [col[1] for col in cursor.fetchall()]

print(f"Current columns in 'user' table: {', '.join(columns)}")

# Check if role_id exists
if 'role_id' in columns:
    print("✓ 'role_id' column already exists in 'user' table.")
    print("No changes needed.")
else:
    print("'role_id' column not found. Adding it...")
    try:
        cursor.execute("ALTER TABLE user ADD COLUMN role_id INTEGER")
        conn.commit()
        print("✓ Successfully added 'role_id' column to 'user' table.")
        
        # Verify it was added
        cursor.execute("PRAGMA table_info(user)")
        new_columns = [col[1] for col in cursor.fetchall()]
        if 'role_id' in new_columns:
            print("✓ Verified: 'role_id' column is now present.")
        else:
            print("⚠️  Warning: Column may not have been added correctly.")
    except Exception as e:
        conn.rollback()
        print(f"❌ Error adding 'role_id' column: {e}")
        exit(1)

# Check if force_password_change exists
if 'force_password_change' in columns:
    print("✓ 'force_password_change' column already exists in 'user' table.")
else:
    print("'force_password_change' column not found. Adding it...")
    try:
        cursor.execute("ALTER TABLE user ADD COLUMN force_password_change BOOLEAN DEFAULT 1")
        conn.commit()
        print("✓ Successfully added 'force_password_change' column to 'user' table.")
    except Exception as e:
        conn.rollback()
        print(f"⚠️  Warning: Could not add 'force_password_change' column: {e}")

conn.close()
print("\n✅ Migration complete!")

