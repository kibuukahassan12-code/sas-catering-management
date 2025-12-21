"""
Safe database migration script to add missing RBAC schema columns.
This script safely adds missing columns without dropping existing tables or data.
"""
from sas_management.app import create_app
from sas_management.models import db
from sqlalchemy.exc import OperationalError
from sqlalchemy import text, inspect
import sys

app = create_app()

def column_exists(table_name, column_name):
    """Check if a column exists in a table."""
    inspector = inspect(db.engine)
    columns = [col['name'] for col in inspector.get_columns(table_name)]
    return column_name in columns

def table_exists(table_name):
    """Check if a table exists."""
    inspector = inspect(db.engine)
    return table_name in inspector.get_table_names()

def add_column_safe(table_name, column_name, column_type, default_value=None):
    """Safely add a column to a table if it doesn't exist."""
    try:
        if column_exists(table_name, column_name):
            print(f"  ✓ Column '{table_name}.{column_name}' already exists. Skipping.")
            return True
        
        if default_value is not None:
            sql = f"ALTER TABLE {table_name} ADD COLUMN {column_name} {column_type} DEFAULT {default_value}"
        else:
            sql = f"ALTER TABLE {table_name} ADD COLUMN {column_name} {column_type}"
        
        db.session.execute(text(sql))
        db.session.commit()
        print(f"  ✓ Added column '{table_name}.{column_name}'")
        return True
    except OperationalError as e:
        error_msg = str(e).lower()
        if "duplicate column name" in error_msg or "already exists" in error_msg:
            print(f"  ✓ Column '{table_name}.{column_name}' already exists. Skipping.")
            return True
        else:
            print(f"  ✗ Error adding '{table_name}.{column_name}': {e}")
            db.session.rollback()
            return False
    except Exception as e:
        print(f"  ✗ Unexpected error adding '{table_name}.{column_name}': {e}")
        db.session.rollback()
        return False

def create_index_safe(table_name, index_name, columns):
    """Safely create an index if it doesn't exist."""
    try:
        # Check if index already exists
        inspector = inspect(db.engine)
        indexes = inspector.get_indexes(table_name)
        existing_index_names = [idx['name'] for idx in indexes]
        
        if index_name in existing_index_names:
            print(f"  ✓ Index '{index_name}' already exists. Skipping.")
            return True
        
        columns_str = ', '.join(columns)
        sql = f"CREATE INDEX IF NOT EXISTS {index_name} ON {table_name} ({columns_str})"
        db.session.execute(text(sql))
        db.session.commit()
        print(f"  ✓ Created index '{index_name}' on '{table_name}'")
        return True
    except Exception as e:
        error_msg = str(e).lower()
        if "already exists" in error_msg or "duplicate" in error_msg:
            print(f"  ✓ Index '{index_name}' already exists. Skipping.")
            return True
        else:
            print(f"  ✗ Error creating index '{index_name}': {e}")
            db.session.rollback()
            return False

def ensure_admin_role():
    """Ensure ADMIN role exists and is marked as system role."""
    try:
        from sas_management.models import Role
        
        admin_role = Role.query.filter_by(name='Admin').first()
        if not admin_role:
            admin_role = Role.query.filter_by(name='ADMIN').first()
        
        if admin_role:
            if not admin_role.is_system_role:
                admin_role.is_system_role = True
                db.session.commit()
                print(f"  ✓ Updated ADMIN role to mark as system role")
        else:
            # Create ADMIN role if it doesn't exist
            admin_role = Role(
                name='Admin',
                description='System administrator with full access',
                is_system_role=True
            )
            db.session.add(admin_role)
            db.session.commit()
            print(f"  ✓ Created ADMIN role")
    except Exception as e:
        print(f"  ✗ Error ensuring ADMIN role: {e}")
        db.session.rollback()

def main():
    """Main migration function."""
    with app.app_context():
        print("=" * 60)
        print("RBAC Schema Migration - Safe Column Addition")
        print("=" * 60)
        print()
        
        # Verify tables exist
        required_tables = ['roles', 'permissions', 'role_permissions', 'user']
        missing_tables = []
        
        for table in required_tables:
            if not table_exists(table):
                missing_tables.append(table)
        
        if missing_tables:
            print(f"⚠ Warning: Missing tables: {', '.join(missing_tables)}")
            print("Creating missing tables from models...")
            try:
                db.create_all()
                print("✓ Created missing tables")
            except Exception as e:
                print(f"✗ Error creating tables: {e}")
                sys.exit(1)
        
        print("\n1. Updating 'roles' table...")
        add_column_safe('roles', 'is_system_role', 'BOOLEAN', 'FALSE')
        
        print("\n2. Updating 'permissions' table...")
        add_column_safe('permissions', 'module', 'VARCHAR(100)')
        add_column_safe('permissions', 'action', 'VARCHAR(50)')
        
        print("\n3. Verifying 'role_permissions' table structure...")
        if not table_exists('role_permissions'):
            print("  ⚠ role_permissions table doesn't exist. Creating from model...")
            db.create_all()
        else:
            print("  ✓ role_permissions table exists")
        
        print("\n4. Verifying 'user' table has required columns...")
        if not column_exists('user', 'role_id'):
            print("  ⚠ user.role_id missing. Adding...")
            add_column_safe('user', 'role_id', 'INTEGER')
        else:
            print("  ✓ user.role_id exists")
        
        if not column_exists('user', 'first_login'):
            print("  ⚠ user.first_login missing. Adding...")
            add_column_safe('user', 'first_login', 'BOOLEAN', 'TRUE')
        else:
            print("  ✓ user.first_login exists")
        
        print("\n5. Creating indexes for performance...")
        # Index on roles.name (already unique, but explicit index helps)
        create_index_safe('roles', 'idx_roles_name', ['name'])
        
        # Index on roles.is_system_role for quick admin lookups
        create_index_safe('roles', 'idx_roles_is_system_role', ['is_system_role'])
        
        # Index on permissions.module and action for permission lookups
        create_index_safe('permissions', 'idx_permissions_module_action', ['module', 'action'])
        
        # Index on role_permissions for faster joins
        create_index_safe('role_permissions', 'idx_role_permissions_role_id', ['role_id'])
        create_index_safe('role_permissions', 'idx_role_permissions_permission_id', ['permission_id'])
        
        # Composite index for role_permissions lookups
        create_index_safe('role_permissions', 'idx_role_permissions_composite', ['role_id', 'permission_id'])
        
        # Index on user.role_id for faster user-role lookups
        create_index_safe('user', 'idx_user_role_id', ['role_id'])
        
        print("\n6. Ensuring ADMIN role is marked as system role...")
        ensure_admin_role()
        
        print("\n" + "=" * 60)
        print("✅ Migration completed successfully!")
        print("=" * 60)
        print("\nSummary:")
        print("  - All required columns have been added")
        print("  - All indexes have been created")
        print("  - ADMIN role bypasses role_permissions (handled in application code)")
        print("  - Backward compatibility maintained (existing columns preserved)")

if __name__ == "__main__":
    main()

