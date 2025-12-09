from app import app, db
from models import User
from sqlalchemy import text

# Run within Flask app context
with app.app_context():
    # Check if role_id column already exists
    with db.engine.connect() as conn:
        # Get table info for user table
        result = conn.execute(text("PRAGMA table_info(user)"))
        columns = [row[1] for row in result.fetchall()]
        
        if "role_id" not in columns:
            print("Adding role_id column to user table...")
            conn.execute(text("ALTER TABLE user ADD COLUMN role_id INTEGER"))
            conn.commit()
            print("✓ role_id column added.")
        else:
            print("✓ role_id column already exists.")
        
        # Update all users to have role_id = 1 (admin role) if it's NULL
        conn.execute(text("UPDATE user SET role_id = 1 WHERE role_id IS NULL"))
        conn.commit()
        print("✓ role_id updated for all users (set to 1 for admin role).")

    print("✓ Fix complete. Database migration successful.")

