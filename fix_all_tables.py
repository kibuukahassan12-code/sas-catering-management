"""
Database migration script to add RBAC support.
Adds role table and role_id to users table.
"""
from app import create_app
from models import db, Role, User
from sqlalchemy import text

def migrate_rbac():
    """Add RBAC tables and columns."""
    app = create_app()
    
    with app.app_context():
        try:
            # Check if role table exists
            inspector = db.inspect(db.engine)
            tables = inspector.get_table_names()
            
            if 'role' not in tables:
                print("Creating 'role' table...")
                db.create_all()
                print("✅ Role table created.")
            else:
                print("✅ Role table already exists.")
            
            # Check if role_id column exists in user table
            user_columns = [col['name'] for col in inspector.get_columns('user')]
            
            if 'role_id' not in user_columns:
                print("Adding 'role_id' column to 'user' table...")
                db.session.execute(text("ALTER TABLE user ADD COLUMN role_id INTEGER REFERENCES role(id)"))
                db.session.commit()
                print("✅ role_id column added to user table.")
            else:
                print("✅ role_id column already exists in user table.")
            
            # Check if force_password_change column exists
            if 'force_password_change' not in user_columns:
                print("Adding 'force_password_change' column to 'user' table...")
                db.session.execute(text("ALTER TABLE user ADD COLUMN force_password_change BOOLEAN DEFAULT 1"))
                db.session.commit()
                print("✅ force_password_change column added to user table.")
            else:
                print("✅ force_password_change column already exists in user table.")
            
            print("\n✅ RBAC and Password System migration completed successfully!")
            print("   Next steps:")
            print("   1. Run: python roles_seed.py")
            print("   2. Assign roles to users via Admin UI")
            print("   3. Create users via Admin → Users → Add User (passwords auto-generated)")
            
        except Exception as e:
            db.session.rollback()
            print(f"❌ Error during migration: {e}")
            import traceback
            traceback.print_exc()
            raise

if __name__ == "__main__":
    migrate_rbac()
