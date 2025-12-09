"""Comprehensive database schema fixer - automatically syncs all models with database."""
import sqlite3
from app import app, db
from sqlalchemy import inspect
from sqlalchemy.exc import OperationalError
from sqlalchemy import text

def get_db_path():
    """Get the actual database path from Flask config."""
    db_uri = app.config.get('SQLALCHEMY_DATABASE_URI', '')
    if db_uri.startswith('sqlite:///'):
        # Extract path from sqlite:///path/to/db
        path = db_uri.replace('sqlite:///', '')
        # Handle absolute paths on Windows
        if path.startswith('/'):
            # On Windows, sqlite:///C:/path becomes /C:/path
            if len(path) > 1 and path[1] == ':':
                return path[1:]  # Remove leading /
        # Handle relative paths
        if not os.path.isabs(path):
            # Check common locations
            possible_paths = [
                path,
                os.path.join('instance', path),
                os.path.join('instance', 'site.db'),
                os.path.join('instance', 'app.db'),
            ]
            for p in possible_paths:
                if os.path.exists(p):
                    return p
        return path
    return None

def get_db_columns_sqlite(table_name, db_path):
    """Get columns from SQLite database using direct connection."""
    try:
        conn = sqlite3.connect(db_path)
        cur = conn.cursor()
        cur.execute(f"PRAGMA table_info({table_name});")
        cols = [col[1] for col in cur.fetchall()]
        conn.close()
        return cols
    except Exception as e:
        print(f"  ⚠ Error getting columns for {table_name}: {e}")
        return []

def get_db_columns_sqlalchemy(table_name, inspector):
    """Get columns using SQLAlchemy inspector."""
    try:
        if table_name not in inspector.get_table_names():
            return []
        return [col['name'] for col in inspector.get_columns(table_name)]
    except Exception as e:
        print(f"  ⚠ Error getting columns for {table_name}: {e}")
        return []

def add_column_sqlite(table_name, column_name, col_type, db_path):
    """Add column using direct SQLite connection."""
    try:
        conn = sqlite3.connect(db_path)
        cur = conn.cursor()
        # Clean column type (remove DEFAULT clauses for SQLite compatibility)
        col_type_clean = col_type.split(" DEFAULT ")[0] if " DEFAULT " in col_type else col_type
        cur.execute(f"ALTER TABLE {table_name} ADD COLUMN {column_name} {col_type_clean};")
        conn.commit()
        conn.close()
        return True, "added"
    except sqlite3.OperationalError as e:
        error_str = str(e).lower()
        if "duplicate" in error_str or "already exists" in error_str:
            return False, "exists"
        return False, f"Error: {str(e)[:50]}"
    except Exception as e:
        return False, f"Error: {str(e)[:50]}"

def add_column_sqlalchemy(table_name, column_name, col_type, db_session):
    """Add column using SQLAlchemy."""
    try:
        # Handle reserved keywords like 'transaction'
        table_name_escaped = f'"{table_name}"' if table_name == 'transaction' else table_name
        col_type_clean = col_type.split(" DEFAULT ")[0] if " DEFAULT " in col_type else col_type
        db_session.execute(text(f"ALTER TABLE {table_name_escaped} ADD COLUMN {column_name} {col_type_clean}"))
        db_session.commit()
        return True, "added"
    except OperationalError as e:
        error_str = str(e).lower()
        if "duplicate" in error_str or "already exists" in error_str:
            return False, "exists"
        try:
            col_type_clean = col_type.split(" DEFAULT ")[0]
            db_session.execute(text(f"ALTER TABLE {table_name_escaped} ADD COLUMN {column_name} {col_type_clean}"))
            db_session.commit()
            return True, "added"
        except:
            return False, f"Error: {str(e)[:50]}"
    except Exception as e:
        return False, f"Error: {str(e)[:50]}"

def get_sqlite_type(sqlalchemy_type):
    """Convert SQLAlchemy type to SQLite type."""
    type_str = str(sqlalchemy_type).lower()
    
    if 'integer' in type_str:
        return 'INTEGER'
    elif 'varchar' in type_str or 'string' in type_str:
        # Extract length if present
        if '(' in type_str:
            length = type_str.split('(')[1].split(')')[0]
            return f'VARCHAR({length})'
        return 'VARCHAR(255)'
    elif 'text' in type_str:
        return 'TEXT'
    elif 'numeric' in type_str or 'decimal' in type_str:
        # Extract precision if present
        if '(' in type_str:
            return f'NUMERIC{type_str.split("(")[1].split(")")[0]}'
        return 'NUMERIC'
    elif 'float' in type_str or 'real' in type_str:
        return 'REAL'
    elif 'boolean' in type_str:
        return 'BOOLEAN'
    elif 'date' in type_str:
        return 'DATE'
    elif 'datetime' in type_str or 'timestamp' in type_str:
        return 'DATETIME'
    else:
        return 'TEXT'  # Default fallback

def fix_table(model, table_name, inspector, db_session, db_path=None):
    """Fix a single table by adding missing columns."""
    print(f"\n{'='*60}")
    print(f"Checking table: {table_name}")
    print(f"{'='*60}")
    
    try:
        # Get model columns
        model_columns = {}
        for col in model.__table__.columns:
            col_type = get_sqlite_type(col.type)
            model_columns[col.name] = col_type
        
        # Always use SQLAlchemy inspector (more reliable)
        db_columns = get_db_columns_sqlalchemy(table_name, inspector)
        
        if not db_columns:
            print(f"  ⚠ Table '{table_name}' does not exist - will be created by db.create_all()")
            return 0
        
        print(f"  Model has {len(model_columns)} columns, DB has {len(db_columns)} columns")
        
        missing_count = 0
        for col_name, col_type in model_columns.items():
            if col_name not in db_columns:
                print(f"  → Missing: {col_name} ({col_type})")
                # Always use SQLAlchemy (more reliable and handles reserved keywords)
                success, message = add_column_sqlalchemy(table_name, col_name, col_type, db_session)
                
                if success:
                    print(f"    ✓ ADDED '{col_name}'")
                    missing_count += 1
                elif message == "exists":
                    print(f"    ✓ '{col_name}' already exists")
                else:
                    print(f"    ✗ Failed: {message}")
            else:
                print(f"  ✓ Exists: {col_name}")
        
        return missing_count
        
    except Exception as e:
        print(f"  ✗ Error fixing table {table_name}: {e}")
        import traceback
        traceback.print_exc()
        return 0

def discover_all_models():
    """Automatically discover all SQLAlchemy models."""
    from sqlalchemy.inspection import inspect as sa_inspect
    models = {}
    
    # Get all models from db.Model registry
    for mapper in db.Model.registry.mappers:
        model = mapper.class_
        if hasattr(model, '__tablename__'):
            table_name = model.__tablename__
            models[table_name] = model
    
    return models

def run_fixer():
    """Main function to fix all database schemas."""
    print("🔧 SAS Management System Database Schema Fixer")
    print("=" * 60)
    print()
    
    with app.app_context():
        inspector = inspect(db.engine)
        db_path = get_db_path()
        
        print(f"📁 Database URI: {app.config.get('SQLALCHEMY_DATABASE_URI', 'N/A')}")
        if db_path and os.path.exists(db_path):
            print(f"📁 Database file: {db_path}")
        print("📁 Using SQLAlchemy inspector")
        print()
        
        # Discover all models automatically
        print("🔍 Discovering all models...")
        all_models = discover_all_models()
        print(f"   Found {len(all_models)} model(s)")
        print()
        
        # Also include manually specified critical models
        critical_models = {
            "user": User,
            "task": Task,
            "event": Event,
            "invoice": Invoice,
            "client": Client,
            "incoming_lead": IncomingLead,
            "inventory_item": InventoryItem,
        }
        
        # Merge with discovered models (discovered takes precedence)
        for table_name, model in critical_models.items():
            if table_name not in all_models:
                all_models[table_name] = model
        
        print(f"📊 Total tables to check: {len(all_models)}")
        print()
        
        total_fixes = 0
        fixed_tables = []
        
        # Fix each table
        for table_name, model in sorted(all_models.items()):
            try:
                fixes = fix_table(model, table_name, inspector, db.session, db_path)
                if fixes > 0:
                    fixed_tables.append((table_name, fixes))
                    total_fixes += fixes
            except Exception as e:
                print(f"  ✗ Error processing {table_name}: {e}")
        
        print()
        print("=" * 60)
        print("📈 SUMMARY")
        print("=" * 60)
        print(f"✅ Checked {len(all_models)} table(s)")
        print(f"✅ Fixed {len(fixed_tables)} table(s)")
        print(f"✅ Added {total_fixes} column(s) total")
        
        if fixed_tables:
            print("\nFixed tables:")
            for table_name, count in fixed_tables:
                print(f"  - {table_name}: {count} column(s)")
        
        print()
        print("=" * 60)
        print("🎉 DATABASE SCHEMA SYNC COMPLETED!")
        print("=" * 60)
        print()
        print("⚠️  IMPORTANT: Restart your Flask application now!")
        print("   The database schema has been updated.")

if __name__ == "__main__":
    # Import all models
    from models import (
        User, Task, Event, Invoice, Client, IncomingLead, InventoryItem,
        Employee, ClientNote, EventDocument, HireOrder, CateringItem,
        BakeryItem, Quotation, Transaction, Journal, Account, POSDevice,
        POSShift, POSOrder, Recipe, ProductionOrder, Ingredient, MenuItem,
        # Add any other models you have
    )
    
    run_fixer()

