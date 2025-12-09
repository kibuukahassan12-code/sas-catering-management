"""Scan ALL models and detect any missing columns automatically."""
from app import app, db
from sqlalchemy import inspect, text
from sqlalchemy.exc import OperationalError
import re

def get_table_columns(inspector, table_name):
    """Get all column names for a table."""
    try:
        if table_name not in inspector.get_table_names():
            return []
        return [col['name'] for col in inspector.get_columns(table_name)]
    except:
        return []

def add_column_safe(table_name, col_name, col_type, inspector, db_session):
    """Safely add a column."""
    try:
        existing = get_table_columns(inspector, table_name)
        if col_name in existing:
            return False, "exists"
        
        # Clean column type for SQLite
        col_type_clean = col_type.split(" DEFAULT ")[0] if " DEFAULT " in col_type else col_type
        
        db_session.execute(text(f"ALTER TABLE {table_name} ADD COLUMN {col_name} {col_type_clean}"))
        db_session.commit()
        return True, "added"
    except OperationalError as e:
        error_str = str(e).lower()
        if "duplicate" in error_str or "already exists" in error_str:
            return False, "exists"
        try:
            col_type_clean = col_type.split(" DEFAULT ")[0]
            db_session.execute(text(f"ALTER TABLE {table_name} ADD COLUMN {col_name} {col_type_clean}"))
            db_session.commit()
            return True, "added"
        except:
            return False, f"Error: {str(e)[:50]}"
    except Exception as e:
        return False, f"Error: {str(e)[:50]}"

def parse_model_file():
    """Parse models.py to extract all model definitions and their columns."""
    models_info = {}
    
    try:
        with open('models.py', 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Find all class definitions that inherit from db.Model
        class_pattern = r'class\s+(\w+)\s*\([^)]*db\.Model[^)]*\):.*?__tablename__\s*=\s*["\'](\w+)["\']'
        classes = re.finditer(class_pattern, content, re.DOTALL)
        
        for match in classes:
            class_name = match.group(1)
            table_name = match.group(2)
            
            # Extract the class body
            class_start = match.end()
            # Find the next class or end of file
            next_class = re.search(r'\nclass\s+\w+', content[class_start:])
            if next_class:
                class_body = content[class_start:class_start + next_class.start()]
            else:
                class_body = content[class_start:]
            
            # Find all db.Column definitions
            column_pattern = r'(\w+)\s*=\s*db\.Column\([^)]+\)'
            columns = re.findall(column_pattern, class_body)
            
            # Also try to get column types for common ones
            created_at_match = re.search(r'created_at\s*=\s*db\.Column\([^)]+\)', class_body)
            updated_at_match = re.search(r'updated_at\s*=\s*db\.Column\([^)]+\)', class_body)
            
            models_info[table_name] = {
                'class_name': class_name,
                'columns': columns,
                'has_created_at': 'created_at' in columns,
                'has_updated_at': 'updated_at' in columns,
            }
    
    except Exception as e:
        print(f"Error parsing models.py: {e}")
    
    return models_info

with app.app_context():
    print("=" * 70)
    print("SCANNING ALL MODELS FOR MISSING COLUMNS")
    print("=" * 70)
    print()
    
    inspector = inspect(db.engine)
    all_tables = inspector.get_table_names()
    
    # Parse models to find what columns should exist
    print("Parsing models.py to find expected columns...")
    models_info = parse_model_file()
    print(f"Found {len(models_info)} model definitions")
    print()
    
    total_fixes = 0
    issues_found = []
    
    # Check each model
    for table_name, info in models_info.items():
        if table_name not in all_tables:
            continue
        
        existing = get_table_columns(inspector, table_name)
        missing = []
        
        # Check for created_at
        if info['has_created_at'] and 'created_at' not in existing:
            missing.append(('created_at', 'DATETIME'))
        
        # Check for updated_at
        if info['has_updated_at'] and 'updated_at' not in existing:
            missing.append(('updated_at', 'DATETIME'))
        
            if missing:
                print(f"⚠ {table_name}: Missing {len(missing)} column(s)")
                for col_name, col_type in missing:
                    # Handle reserved keywords like 'transaction'
                    table_name_escaped = f'"{table_name}"' if table_name == 'transaction' else table_name
                    try:
                        existing = get_table_columns(inspector, table_name)
                        if col_name in existing:
                            print(f"  ✓ '{col_name}' already exists")
                            continue
                        
                        col_type_clean = col_type.split(" DEFAULT ")[0] if " DEFAULT " in col_type else col_type
                        db.session.execute(text(f"ALTER TABLE {table_name_escaped} ADD COLUMN {col_name} {col_type_clean}"))
                        db.session.commit()
                        print(f"  ✓ ADDED '{col_name}'")
                        total_fixes += 1
                    except Exception as e:
                        error_str = str(e).lower()
                        if "duplicate" in error_str or "already exists" in error_str:
                            print(f"  ✓ '{col_name}' already exists")
                        else:
                            print(f"  ✗ Failed to add '{col_name}': {str(e)[:50]}")
                            issues_found.append((table_name, col_name))
                print()
    
    # Also check known critical tables manually
    print("Checking known critical tables...")
    critical_tables = {
        "task": [("created_at", "DATETIME")],
        "inventory_item": [("description", "TEXT"), ("unit_price_ugx", "NUMERIC(12,2)")],
        "incoming_lead": [("email", "VARCHAR(120)")],
    }
    
    for table_name, fixes in critical_tables.items():
        if table_name not in all_tables:
            continue
        existing = get_table_columns(inspector, table_name)
        for col_name, col_type in fixes:
            if col_name not in existing:
                success, message = add_column_safe(table_name, col_name, col_type, inspector, db.session)
                if success:
                    print(f"  ✓ ADDED '{table_name}.{col_name}'")
                    total_fixes += 1
    
    print()
    print("=" * 70)
    print("TESTING CRITICAL QUERIES...")
    print("=" * 70)
    
    # Test all critical queries
    test_results = []
    
    queries_to_test = [
        ("InventoryItem", "InventoryItem.query.filter(InventoryItem.stock_count <= 10).count()"),
        ("IncomingLead", "IncomingLead.query.filter_by(pipeline_stage='New Lead').count()"),
        ("User", "User.query.count()"),
        ("Client", "Client.query.filter(Client.is_archived == False).count()"),
        ("Event", "Event.query.count()"),
        ("Task", "Task.query.filter(Task.due_date <= date.today()).filter(Task.status != 'Complete').count()"),
    ]
    
    for test_name, query_str in queries_to_test:
        try:
            from models import InventoryItem, IncomingLead, User, Client, Event, Task
            from datetime import date
            result = eval(query_str)
            test_results.append((test_name, True, f"{result}"))
        except Exception as e:
            test_results.append((test_name, False, str(e)[:100]))
    
    print()
    all_passed = True
    for test_name, passed, message in test_results:
        status = "✓" if passed else "✗"
        print(f"{status} {test_name}: {message}")
        if not passed:
            all_passed = False
    
    print()
    print("=" * 70)
    if all_passed and total_fixes == 0:
        print("✅ ALL MODELS SYNCED! No missing columns found.")
    elif all_passed:
        print(f"✅ ALL TESTS PASSED! Applied {total_fixes} fix(es).")
    else:
        print(f"⚠️  SOME TESTS FAILED! Applied {total_fixes} fix(es).")
        if issues_found:
            print(f"   Issues found: {issues_found}")
    print("=" * 70)
    print()
    print("⚠️  IMPORTANT: Restart your Flask application NOW!")

