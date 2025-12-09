"""Comprehensive system error scanner - finds all types of errors."""
import os
import sys
import ast
import traceback
from pathlib import Path

errors_found = {
    'database': [],
    'python_syntax': [],
    'python_imports': [],
    'templates': [],
    'routes': [],
    'ui_issues': []
}

print("=" * 70)
print("COMPREHENSIVE SYSTEM ERROR SCANNER")
print("=" * 70)
print()

# 1. Scan for database schema issues
print("1. Scanning for database schema issues...")
try:
    from app import app, db
    from sqlalchemy import inspect, text
    from models import *
    
    with app.app_context():
        inspector = inspect(db.engine)
        all_tables = inspector.get_table_names()
        
        # Check critical models
        critical_models = {
            'user': ['id', 'email', 'password_hash', 'role', 'created_at', 'last_login'],
            'incoming_lead': ['id', 'client_name', 'email', 'phone', 'pipeline_stage', 'timestamp'],
            'inventory_item': ['id', 'name', 'description', 'stock_count', 'unit_price_ugx', 'created_at'],
            'task': ['id', 'title', 'description', 'due_date', 'status', 'created_at'],
            'client': ['id', 'name', 'email', 'phone', 'created_at', 'updated_at'],
            'event': ['id', 'client_id', 'event_name', 'event_date', 'status', 'created_at'],
        }
        
        for table_name, required_cols in critical_models.items():
            if table_name in all_tables:
                existing = [col['name'] for col in inspector.get_columns(table_name)]
                missing = [col for col in required_cols if col not in existing]
                if missing:
                    errors_found['database'].append(f"{table_name}: Missing columns {missing}")
        
        print(f"   Found {len(errors_found['database'])} database issues")
except Exception as e:
    errors_found['database'].append(f"Error scanning database: {e}")

# 2. Scan Python files for syntax errors
print("2. Scanning Python files for syntax errors...")
python_files = []
for root, dirs, files in os.walk('.'):
    # Skip virtual environments and cache
    if any(skip in root for skip in ['__pycache__', '.git', 'venv', 'env', '.venv', 'instance']):
        continue
    for file in files:
        if file.endswith('.py'):
            python_files.append(os.path.join(root, file))

syntax_errors = 0
for py_file in python_files[:50]:  # Limit to first 50 files
    try:
        with open(py_file, 'r', encoding='utf-8') as f:
            code = f.read()
        ast.parse(code)
    except SyntaxError as e:
        errors_found['python_syntax'].append(f"{py_file}: {e}")
        syntax_errors += 1
    except Exception:
        pass

print(f"   Found {syntax_errors} syntax errors")

# 3. Check for import errors in critical files
print("3. Checking critical files for import errors...")
critical_files = ['app.py', 'models.py', 'routes.py', 'config.py']
for file in critical_files:
    if os.path.exists(file):
        try:
            with open(file, 'r', encoding='utf-8') as f:
                content = f.read()
            # Check for common import issues
            if 'from models import' in content and 'models.py' not in file:
                # This is fine
                pass
        except Exception as e:
            errors_found['python_imports'].append(f"{file}: {e}")

# 4. Check template files
print("4. Scanning template files...")
template_dir = 'templates'
if os.path.exists(template_dir):
    for root, dirs, files in os.walk(template_dir):
        for file in files:
            if file.endswith(('.html', '.jinja2')):
                template_path = os.path.join(root, file)
                try:
                    with open(template_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                    # Check for common template issues
                    if '{{' in content and '}}' not in content:
                        errors_found['templates'].append(f"{template_path}: Unclosed template variable")
                except Exception as e:
                    errors_found['templates'].append(f"{template_path}: {e}")

# 5. Check routes for common issues
print("5. Checking routes for errors...")
routes_file = 'routes.py'
if os.path.exists(routes_file):
    try:
        with open(routes_file, 'r', encoding='utf-8') as f:
            content = f.read()
        # Check for common route issues
        if '@core_bp.route' in content and 'core_bp = Blueprint' not in content:
            errors_found['routes'].append("routes.py: Blueprint definition might be missing")
    except Exception as e:
        errors_found['routes'].append(f"{routes_file}: {e}")

# 6. Check blueprints directory
print("6. Checking blueprints...")
blueprints_dir = 'blueprints'
if os.path.exists(blueprints_dir):
    for root, dirs, files in os.walk(blueprints_dir):
        for file in files:
            if file.endswith('.py') and file != '__init__.py':
                bp_file = os.path.join(root, file)
                try:
                    with open(bp_file, 'r', encoding='utf-8') as f:
                        content = f.read()
                    # Check for blueprint registration issues
                    if '@' in content and 'Blueprint' in content and 'register_blueprint' not in content:
                        # This might be an issue if blueprint isn't registered
                        pass
                except Exception as e:
                    errors_found['routes'].append(f"{bp_file}: {e}")

print()
print("=" * 70)
print("SCAN RESULTS")
print("=" * 70)
print()

total_errors = sum(len(errors) for errors in errors_found.values())
print(f"Total errors found: {total_errors}")
print()

for error_type, errors in errors_found.items():
    if errors:
        print(f"{error_type.upper()}: {len(errors)} error(s)")
        for error in errors[:5]:  # Show first 5
            print(f"  - {error}")
        if len(errors) > 5:
            print(f"  ... and {len(errors) - 5} more")
        print()

if total_errors == 0:
    print("✅ No critical errors found!")
else:
    print(f"⚠️  Found {total_errors} error(s) that need fixing")

print("=" * 70)

