"""
Migration script to add RBAC tables and update user table.
This script creates the roles, permissions, and role_permissions tables,
and updates the user table to add role_id and force_password_change columns.
"""
import sqlite3
import os

# Get the database path
db_path = os.path.join("instance", "site.db")
if not os.path.exists(db_path):
    print(f"Database not found at {db_path}. Creating new database structure...")
    print("Please run the app once to create the database, then run this migration.")
    exit(1)

print(f"Connecting to database at {db_path}...")
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

print("Starting RBAC migration...")
print("=" * 60)

# Step 1: Rename old role table if it exists (backup)
try:
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='role'")
    if cursor.fetchone():
        cursor.execute("ALTER TABLE role RENAME TO role_old")
        conn.commit()
        print("[OK] Renamed old 'role' table to 'role_old' (backup)")
except Exception as e:
    print(f"  Note: {e}")

# Step 2: Rename old permission table if it exists (backup)
try:
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='permission'")
    if cursor.fetchone():
        cursor.execute("ALTER TABLE permission RENAME TO permission_old")
        conn.commit()
        print("[OK] Renamed old 'permission' table to 'permission_old' (backup)")
except Exception as e:
    print(f"  Note: {e}")

# Step 3: Create roles table
try:
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS roles (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name VARCHAR(100) UNIQUE NOT NULL,
            description TEXT,
            created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    print("[OK] Created table 'roles'")
except Exception as e:
    print(f"  Error creating 'roles' table: {e}")
    conn.rollback()

# Step 4: Create permissions table
try:
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS permissions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name VARCHAR(200) UNIQUE NOT NULL,
            module VARCHAR(100) NOT NULL,
            action VARCHAR(100) NOT NULL,
            created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
        )
    """)
    # Create index on module for faster queries
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_permissions_module 
        ON permissions(module)
    """)
    conn.commit()
    print("[OK] Created table 'permissions'")
except Exception as e:
    print(f"  Error creating 'permissions' table: {e}")
    conn.rollback()

# Step 5: Create role_permissions junction table
try:
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS role_permissions (
            role_id INTEGER NOT NULL,
            permission_id INTEGER NOT NULL,
            created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY (role_id, permission_id),
            FOREIGN KEY (role_id) REFERENCES roles(id) ON DELETE CASCADE,
            FOREIGN KEY (permission_id) REFERENCES permissions(id) ON DELETE CASCADE
        )
    """)
    conn.commit()
    print("[OK] Created table 'role_permissions'")
except Exception as e:
    print(f"  Error creating 'role_permissions' table: {e}")
    conn.rollback()

# Step 6: Update user table - add role_id column if it doesn't exist
try:
    cursor.execute("PRAGMA table_info(user)")
    columns = [col[1] for col in cursor.fetchall()]
    if 'role_id' not in columns:
        cursor.execute("ALTER TABLE user ADD COLUMN role_id INTEGER")
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_user_role_id 
            ON user(role_id)
        """)
        conn.commit()
        print("[OK] Added 'role_id' column to 'user' table")
    else:
        print("[OK] 'role_id' column already exists in 'user' table")
except Exception as e:
    print(f"  Error adding 'role_id' column: {e}")
    conn.rollback()

# Step 7: Update user table - add force_password_change column if it doesn't exist
try:
    cursor.execute("PRAGMA table_info(user)")
    columns = [col[1] for col in cursor.fetchall()]
    if 'force_password_change' not in columns:
        cursor.execute("ALTER TABLE user ADD COLUMN force_password_change BOOLEAN DEFAULT 1")
        conn.commit()
        print("[OK] Added 'force_password_change' column to 'user' table")
    else:
        print("[OK] 'force_password_change' column already exists in 'user' table")
except Exception as e:
    print(f"  Error adding 'force_password_change' column: {e}")
    conn.rollback()

# Step 8: Add foreign key constraint for role_id (if supported)
try:
    # SQLite doesn't support adding foreign keys to existing tables easily
    # The foreign key relationship is handled at the application level
    print("[OK] Foreign key relationships will be enforced at application level")
except Exception as e:
    print(f"  Note: {e}")

print("\n" + "=" * 60)
print("✅ RBAC Migration Complete!")
print("\nNext steps:")
print("1. Run 'python seed_rbac.py' to populate default roles and permissions")
print("2. Access /admin/roles to manage roles and permissions")
print("3. Access /admin/user-roles to assign roles to users")

conn.close()

