"""Database Auto-Fix System - Automatically adds missing columns to match SQLAlchemy models."""
import os
import sqlite3
from pathlib import Path
import sys
from decimal import Decimal

# Add parent directory to path
BASE_DIR = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(BASE_DIR))


class SchemaValidationResult:
    """Result of schema validation."""
    def __init__(self):
        self.is_valid = True
        self.is_partially_valid = False
        self.critical_missing = []  # List of (table, column) tuples
        self.non_critical_missing = []  # List of (table, column) tuples
        self.type_mismatches = []  # List of (table, column, model_type, db_type) tuples
        self.failed_fixes = []  # List of (table, column, error) tuples


def get_sqlalchemy_type(column):
    """Convert SQLAlchemy column type to SQLite type."""
    type_str = str(column.type)
    
    # Handle common SQLAlchemy types
    if 'INTEGER' in type_str.upper() or 'INT' in type_str.upper():
        return "INTEGER"
    elif 'NUMERIC' in type_str.upper() or 'DECIMAL' in type_str.upper():
        # Extract precision if available
        if '(' in type_str:
            return type_str.split('(')[0].upper() + "(" + type_str.split('(')[1].split(')')[0] + ")"
        return "NUMERIC(14,2)"
    elif 'FLOAT' in type_str.upper() or 'REAL' in type_str.upper():
        return "REAL"
    elif 'DATE' in type_str.upper():
        return "DATE"
    elif 'DATETIME' in type_str.upper() or 'TIMESTAMP' in type_str.upper():
        return "DATETIME"
    elif 'BOOLEAN' in type_str.upper() or 'BOOL' in type_str.upper():
        return "INTEGER"  # SQLite uses INTEGER for boolean
    elif 'TEXT' in type_str.upper() or 'VARCHAR' in type_str.upper() or 'STRING' in type_str.upper():
        return "TEXT"
    else:
        # Default to TEXT for unknown types
        return "TEXT"


def get_model_columns(model):
    """Read SQLAlchemy model column names and types."""
    columns = {}
    for column in model.__table__.columns:
        col_type = get_sqlalchemy_type(column)
        # Add DEFAULT if column has a default
        default = ""
        if column.default is not None:
            if hasattr(column.default, 'arg'):
                if isinstance(column.default.arg, (int, float, Decimal)):
                    default = f" DEFAULT {column.default.arg}"
                elif isinstance(column.default.arg, str):
                    # Escape single quotes in default strings
                    escaped = column.default.arg.replace("'", "''")
                    default = f" DEFAULT '{escaped}'"
        columns[column.name] = {
            'type': col_type,
            'default': default,
            'nullable': column.nullable,
            'primary_key': column.primary_key
        }
    return columns


def get_table_columns(cursor, table):
    """Get actual DB columns."""
    try:
        cursor.execute(f"PRAGMA table_info('{table}')")
        return {row[1]: row[2] for row in cursor.fetchall()}  # Return dict with name:type
    except Exception as e:
        print(f"[ERROR] Could not get columns for table {table}: {e}")
        return {}


def add_column(cursor, table, column_name, column_info, validation_result):
    """
    Add missing column using SQLite-safe syntax.
    Generates ONE ADD COLUMN per statement with no trailing commas.
    """
    try:
        sql_type = column_info['type']
        default_clause = column_info.get('default', '')
        
        # SQLite-safe ALTER TABLE: ONE column per statement, no trailing commas
        sql = f"ALTER TABLE {table} ADD COLUMN {column_name} {sql_type}"
        if default_clause:
            sql += default_clause
        
        # Ensure no trailing commas or semicolons in the statement itself
        sql = sql.rstrip(';').rstrip(',')
        
        cursor.execute(sql)
        print(f"[OK] Added column '{column_name}' ({sql_type}) to table '{table}'")
        return True
    except sqlite3.OperationalError as e:
        error_msg = str(e).lower()
        if "duplicate column" in error_msg or "already exists" in error_msg:
            print(f"[INFO] Column '{column_name}' already exists in table '{table}'")
            return False
        else:
            error_msg_full = f"Could not add column {column_name} to {table}: {e}"
            print(f"[ERROR] {error_msg_full}")
            validation_result.failed_fixes.append((table, column_name, str(e)))
            validation_result.is_valid = False
            return False
    except Exception as e:
        error_msg_full = f"Unexpected error adding column {column_name} to {table}: {e}"
        print(f"[ERROR] {error_msg_full}")
        validation_result.failed_fixes.append((table, column_name, str(e)))
        validation_result.is_valid = False
        return False


def validate_schema(cursor, models_to_check, validation_result):
    """
    Validate schema after auto-fix by comparing model columns vs actual DB columns.
    """
    print("\n[VALIDATION] Starting schema validation...")
    
    for model_name, model in models_to_check:
        try:
            table = model.__tablename__
            
            # Check if table exists
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name=?", (table,))
            if not cursor.fetchone():
                print(f"[WARNING] Table '{table}' does not exist")
                continue
            
            model_cols = get_model_columns(model)
            db_cols = get_table_columns(cursor, table)
            
            # Check for missing columns
            for col_name, col_info in model_cols.items():
                if col_name not in db_cols:
                    # Determine if critical (primary key or not nullable without default)
                    is_critical = (
                        col_info.get('primary_key', False) or
                        (not col_info.get('nullable', True) and not col_info.get('default'))
                    )
                    
                    if is_critical:
                        validation_result.critical_missing.append((table, col_name))
                        validation_result.is_valid = False
                    else:
                        validation_result.non_critical_missing.append((table, col_name))
                        validation_result.is_partially_valid = True
            
            # Check for type mismatches (SQLite-safe check)
            for col_name, col_info in model_cols.items():
                if col_name in db_cols:
                    model_type = col_info['type'].upper()
                    db_type = (db_cols[col_name] or "").upper()
                    
                    # Normalize types for comparison
                    if not db_type:
                        db_type = "TEXT"
                    
                    # Check for significant mismatches (not perfect, but SQLite-safe)
                    if model_type not in db_type and db_type not in model_type:
                        # Allow some flexibility (INTEGER vs INT, TEXT vs VARCHAR)
                        if not (
                            ('INTEGER' in model_type and 'INT' in db_type) or
                            ('INT' in model_type and 'INTEGER' in db_type) or
                            ('TEXT' in model_type and ('TEXT' in db_type or 'VARCHAR' in db_type)) or
                            ('TEXT' in db_type and ('TEXT' in model_type or 'VARCHAR' in model_type))
                        ):
                            validation_result.type_mismatches.append((table, col_name, model_type, db_type))
                            validation_result.is_partially_valid = True
                            
        except Exception as e:
            print(f"[ERROR] Error validating model {model_name}: {e}")
            continue
    
    return validation_result


def auto_fix_schema(db_path=None, models_module=None, app=None):
    """
    Auto-fix database schema by adding missing columns.
    
    Args:
        db_path: Path to database file (optional, will auto-detect)
        models_module: Module containing models (optional, will auto-import)
        app: Flask app instance (optional, for logging)
    
    Returns:
        SchemaValidationResult object with validation status
    """
    validation_result = SchemaValidationResult()
    logger = app.logger if app else None
    
    def log(level, message):
        """Log message to both print and app logger."""
        print(message)
        if logger:
            if level == 'ERROR':
                logger.error(message)
            elif level == 'WARNING':
                logger.warning(message)
            elif level == 'INFO':
                logger.info(message)
    
    log('INFO', "[INFO] Starting DB Auto-Fix System")
    
    # Ensure db_path is a Path object
    if isinstance(db_path, str):
        db_path = Path(db_path)
    
    # Auto-detect DB path
    if db_path is None:
        # Try multiple possible locations
        possible_paths = [
            BASE_DIR / "sas_management" / "instance" / "sas.db",
            BASE_DIR / "instance" / "sas.db",
            BASE_DIR / "sas_management" / "instance" / "app.db",
            BASE_DIR / "instance" / "app.db",
        ]
        
        db_path = None
        for path in possible_paths:
            if path.exists():
                db_path = path
                break
        
        if db_path is None:
            log('WARNING', "[WARNING] Database file not found. Will be created by db.create_all()")
            return validation_result
    
    # Ensure db_path is Path object (in case it was set above)
    if isinstance(db_path, str):
        db_path = Path(db_path)
    
    log('INFO', f"[INFO] Database: {db_path}")
    
    if not db_path.exists():
        log('INFO', "[INFO] Database file does not exist yet. Will be created by db.create_all()")
        return validation_result
    
    try:
        conn = sqlite3.connect(str(db_path))
        cur = conn.cursor()
        
        # Import models
        if models_module is None:
            try:
                from sas_management.models import db
                # Get all models from the models module
                import sas_management.models as models_module
            except ImportError as e:
                log('ERROR', f"[ERROR] Could not import models: {e}")
                conn.close()
                validation_result.is_valid = False
                return validation_result
        
        # Get all model classes
        models_to_check = []
        for attr_name in dir(models_module):
            attr = getattr(models_module, attr_name)
            if (isinstance(attr, type) and 
                hasattr(attr, '__tablename__') and 
                hasattr(attr, '__table__') and
                issubclass(attr, db.Model)):
                models_to_check.append((attr_name, attr))
        
        if not models_to_check:
            log('WARNING', "[WARNING] No models found to check")
            conn.close()
            return validation_result
        
        log('INFO', f"[INFO] Found {len(models_to_check)} models to check")
        
        total_added = 0
        total_failed = 0
        
        # Tables excluded from auto-fix (must be migrated manually)
        EXCLUDED_TABLES = {
            'service_events',
            'service_event_items',
            'service_staff_assignments',
            'service_checklist_items'
        }
        
        for model_name, model in models_to_check:
            try:
                table = model.__tablename__
                
                # Skip excluded tables - these must be migrated manually
                if table in EXCLUDED_TABLES:
                    log('INFO', f"[SKIP] Table '{table}' is excluded from auto-fix (use manual migration script)")
                    continue
                
                # Check if table exists
                cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name=?", (table,))
                if not cur.fetchone():
                    log('INFO', f"[INFO] Table '{table}' does not exist (will be created by db.create_all())")
                    continue
                
                model_cols = get_model_columns(model)
                db_cols = get_table_columns(cur, table)
                
                missing_cols = {col: col_info for col, col_info in model_cols.items() if col not in db_cols}
                
                if missing_cols:
                    log('INFO', f"\n[CHECK] Table: {table} ({model_name})")
                    log('INFO', f"  Missing columns: {list(missing_cols.keys())}")
                    
                    for col_name, col_info in missing_cols.items():
                        if add_column(cur, table, col_name, col_info, validation_result):
                            total_added += 1
                        else:
                            total_failed += 1
                else:
                    log('INFO', f"[OK] Table '{table}' ({model_name}) - all columns present")
                    
            except Exception as e:
                error_msg = f"[ERROR] Error checking model {model_name}: {e}"
                log('ERROR', error_msg)
                validation_result.is_valid = False
                continue
        
        conn.commit()
        
        # Run schema validation AFTER auto-fix
        validation_result = validate_schema(cur, models_to_check, validation_result)
        
        conn.close()
        
        # Report results
        if total_failed > 0:
            log('ERROR', f"\n[ERROR] Auto-Fix Complete: {total_added} column(s) added, {total_failed} FAILED")
            validation_result.is_valid = False
        elif total_added > 0:
            log('INFO', f"\n[OK] Auto-Fix Complete: Added {total_added} missing column(s)")
        else:
            log('INFO', f"\n[OK] Auto-Fix Complete: All tables are synchronized with models")
        
        # Only report "schema synchronized" if truly synchronized
        if validation_result.is_valid and total_failed == 0:
            log('INFO', "[INFO] Database schema is now synchronized. No 'no such column' errors!")
        else:
            log('WARNING', "[WARNING] Database schema may have issues. See validation results above.")
        
        return validation_result
        
    except Exception as e:
        error_msg = f"[ERROR] Auto-fix failed: {e}"
        log('ERROR', error_msg)
        import traceback
        traceback.print_exc()
        validation_result.is_valid = False
        return validation_result


def print_health_banner(validation_result):
    """Print a consolidated health report banner."""
    print("\n" + "="*70)
    print("DATABASE SCHEMA HEALTH REPORT")
    print("="*70)
    
    if validation_result.is_valid:
        print("✅ Schema Status: VALID")
    elif validation_result.critical_missing:
        print("❌ Schema Status: INVALID (Critical columns missing)")
    else:
        print("⚠️  Schema Status: PARTIALLY VALID (Non-critical issues)")
    
    if validation_result.critical_missing:
        print("\n🔴 CRITICAL ISSUES:")
        for table, column in validation_result.critical_missing:
            print(f"   • {table}.{column} - MISSING (CRITICAL)")
    
    if validation_result.non_critical_missing:
        print("\n🟡 NON-CRITICAL ISSUES:")
        for table, column in validation_result.non_critical_missing:
            print(f"   • {table}.{column} - MISSING")
    
    if validation_result.type_mismatches:
        print("\n🟡 TYPE MISMATCHES:")
        for table, column, model_type, db_type in validation_result.type_mismatches:
            print(f"   • {table}.{column} - Model: {model_type}, DB: {db_type}")
    
    if validation_result.failed_fixes:
        print("\n🔴 FAILED FIXES:")
        for table, column, error in validation_result.failed_fixes:
            print(f"   • {table}.{column} - {error}")
    
    if validation_result.critical_missing or validation_result.failed_fixes:
        print("\n⚠️  ACTION REQUIRED:")
        print("   • Run manual migration to fix critical issues")
        print("   • Affected modules may be unavailable")
        print("   • Check logs for detailed error messages")
    elif validation_result.non_critical_missing or validation_result.type_mismatches:
        print("\n💡 RECOMMENDATION:")
        print("   • Schema is functional but has minor issues")
        print("   • Consider running manual migration for optimal performance")
    else:
        print("\n✅ All systems operational")
    
    print("="*70 + "\n")


if __name__ == "__main__":
    result = auto_fix_schema()
    print_health_banner(result)
