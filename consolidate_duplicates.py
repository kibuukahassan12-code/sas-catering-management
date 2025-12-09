#!/usr/bin/env python3
"""
Script to consolidate duplicate functions across blueprints.
Safely removes duplicate definitions and adds imports from utils.
"""

import os
import re
from pathlib import Path

# Files that need special handling (keep their custom implementations)
SPECIAL_FILES = {
    'blueprints/pos/__init__.py': {
        'reason': 'Has custom role_required with authentication checks',
        'keep': ['role_required']
    }
}

def find_function_definition(content, func_name):
    """Find the start and end of a function definition."""
    pattern = rf'^def {re.escape(func_name)}\([^)]*\):.*?(?=^def |^@|\Z)'
    match = re.search(pattern, content, re.MULTILINE | re.DOTALL)
    if match:
        return match.start(), match.end()
    return None, None

def remove_function_definition(content, func_name):
    """Remove a function definition from content."""
    start, end = find_function_definition(content, func_name)
    if start is not None and end is not None:
        # Remove the function and any trailing blank lines
        removed = content[start:end]
        content = content[:start] + content[end:]
        # Clean up extra blank lines
        content = re.sub(r'\n\n\n+', '\n\n', content)
        return content, True
    return content, False

def has_function_definition(content, func_name):
    """Check if content has a function definition."""
    pattern = rf'^def {re.escape(func_name)}\('
    return bool(re.search(pattern, content, re.MULTILINE))

def get_imports_needed(content, filepath):
    """Determine which imports are needed from utils."""
    needed = []
    
    # Check for each function
    if has_function_definition(content, 'role_required'):
        if filepath not in SPECIAL_FILES or 'role_required' not in SPECIAL_FILES[filepath].get('keep', []):
            needed.append('role_required')
    
    if has_function_definition(content, '_get_decimal'):
        needed.append('_get_decimal')
    
    if has_function_definition(content, '_paginate_query'):
        needed.append('_paginate_query')
    
    if has_function_definition(content, '_parse_date'):
        needed.append('_parse_date')
    
    if has_function_definition(content, 'allowed_file'):
        needed.append('allowed_file')
    
    return needed

def add_utils_import(content, imports_needed):
    """Add utils import if not already present."""
    if not imports_needed:
        return content, False
    
    # Check if utils import already exists
    if 'from utils import' in content:
        # Check if all needed imports are already there
        utils_import_match = re.search(r'from utils import ([^\n]+)', content)
        if utils_import_match:
            existing_imports = [imp.strip() for imp in utils_import_match.group(1).split(',')]
            missing = [imp for imp in imports_needed if imp not in existing_imports]
            if missing:
                # Add missing imports
                new_imports = ', '.join(existing_imports + missing)
                content = content.replace(utils_import_match.group(0), f'from utils import {new_imports}')
                return content, True
        return content, False
    
    # Find the best place to insert the import
    # Look for other imports from local modules
    import_pattern = r'(from (?:models|services|blueprints)\.[^\n]+\n)'
    matches = list(re.finditer(import_pattern, content))
    
    if matches:
        # Insert after the last local import
        last_match = matches[-1]
        insert_pos = last_match.end()
        import_line = f"from utils import {', '.join(imports_needed)}\n"
        content = content[:insert_pos] + import_line + content[insert_pos:]
    else:
        # Look for any import statement
        import_pattern = r'(^from [^\n]+\n|^import [^\n]+\n)'
        matches = list(re.finditer(import_pattern, content, re.MULTILINE))
        if matches:
            last_match = matches[-1]
            insert_pos = last_match.end()
            import_line = f"from utils import {', '.join(imports_needed)}\n"
            content = content[:insert_pos] + import_line + content[insert_pos:]
        else:
            # Insert at the beginning after any docstring
            docstring_end = 0
            if content.startswith('"""') or content.startswith("'''"):
                docstring_match = re.search(r'""".*?"""|\'\'\'.*?\'\'\'', content, re.DOTALL)
                if docstring_match:
                    docstring_end = docstring_match.end()
            import_line = f"from utils import {', '.join(imports_needed)}\n\n"
            content = content[:docstring_end] + import_line + content[docstring_end:]
    
    return content, True

def remove_unused_imports(content):
    """Remove unused imports like functools.wraps if wraps is not used."""
    # Check if wraps is used
    if 'wraps(' not in content and 'from functools import wraps' in content:
        content = re.sub(r'from functools import wraps\n', '', content)
        content = re.sub(r'from functools import wraps, ', 'from functools import ', content)
        content = re.sub(r', wraps', '', content)
        # If functools import is now empty, remove it
        content = re.sub(r'from functools import\s*\n', '', content)
    
    # Remove unused current_user if not used
    if 'current_user' not in content and 'from flask_login import current_user' in content:
        content = re.sub(r', current_user', '', content)
        content = re.sub(r'current_user, ', '', content)
        content = re.sub(r'from flask_login import current_user\n', '', content)
    
    # Remove unused current_app if not used (but be careful - it might be used in templates)
    if 'current_app' not in content and 'from flask import.*current_app' in content:
        content = re.sub(r', current_app', '', content)
        content = re.sub(r'current_app, ', '', content)
    
    return content

def update_file(filepath):
    """Update a single file to use shared utilities."""
    filepath_str = str(filepath)
    
    # Skip special files or handle them specially
    if filepath_str in SPECIAL_FILES:
        special_config = SPECIAL_FILES[filepath_str]
        keep_functions = special_config.get('keep', [])
        print(f"⚠️  Skipping {filepath_str} - {special_config.get('reason', 'Special handling required')}")
        return False
    
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        original_content = content
        imports_needed = get_imports_needed(content, filepath_str)
        
        if not imports_needed:
            return False  # No duplicates to remove
        
        # Remove function definitions (except those to keep)
        for func_name in imports_needed:
            if filepath_str in SPECIAL_FILES and func_name in SPECIAL_FILES[filepath_str].get('keep', []):
                continue
            content, removed = remove_function_definition(content, func_name)
            if removed:
                print(f"  ✓ Removed {func_name}")
        
        # Add utils import
        content, added = add_utils_import(content, imports_needed)
        if added:
            print(f"  ✓ Added utils import")
        
        # Clean up unused imports
        content = remove_unused_imports(content)
        
        # Only write if content changed
        if content != original_content:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)
            return True
        
        return False
    except Exception as e:
        print(f"  ✗ Error: {e}")
        return False

def main():
    """Main function to update all blueprint files."""
    print("=" * 80)
    print("Consolidating Duplicate Functions")
    print("=" * 80)
    print()
    
    # Find all Python files in blueprints directory
    blueprint_files = []
    for root, dirs, files in os.walk('blueprints'):
        # Skip __pycache__
        if '__pycache__' in root:
            continue
        for file in files:
            if file.endswith('.py') and file != '__init__.py':
                blueprint_files.append(os.path.join(root, file))
            elif file == '__init__.py':
                blueprint_files.append(os.path.join(root, file))
    
    # Also check routes.py
    if os.path.exists('routes.py'):
        blueprint_files.append('routes.py')
    
    updated_count = 0
    skipped_count = 0
    
    for filepath in sorted(blueprint_files):
        filepath_str = str(filepath)
        print(f"Processing: {filepath_str}")
        
        if filepath_str in SPECIAL_FILES:
            skipped_count += 1
            continue
        
        if update_file(filepath):
            updated_count += 1
            print(f"  ✓ Updated")
        else:
            print(f"  - No changes needed")
        print()
    
    print("=" * 80)
    print(f"Summary: {updated_count} files updated, {skipped_count} files skipped")
    print("=" * 80)

if __name__ == '__main__':
    main()

