#!/usr/bin/env python3
"""
Script to update blueprints to use shared utilities.
This script removes duplicate function definitions and adds imports from utils.
"""

import re
import os

# Files that need special handling (e.g., POS has custom role_required)
SPECIAL_FILES = {
    'blueprints/pos/__init__.py': 'has_custom_role_required',
}

def update_file(filepath):
    """Update a single file to use shared utilities."""
    if filepath in SPECIAL_FILES:
        return False  # Skip special files
    
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        original_content = content
        needs_update = False
        
        # Check if file has role_required
        has_role_required = bool(re.search(r'^def role_required\(', content, re.MULTILINE))
        # Check if file has _get_decimal
        has_get_decimal = bool(re.search(r'^def _get_decimal\(', content, re.MULTILINE))
        # Check if file has _paginate_query
        has_paginate = bool(re.search(r'^def _paginate_query\(', content, re.MULTILINE))
        # Check if file has _parse_date
        has_parse_date = bool(re.search(r'^def _parse_date\(', content, re.MULTILINE))
        # Check if file has allowed_file
        has_allowed_file = bool(re.search(r'^def allowed_file\(', content, re.MULTILINE))
        
        if not (has_role_required or has_get_decimal or has_paginate or has_parse_date or has_allowed_file):
            return False  # No duplicates to remove
        
        # Remove role_required definition
        if has_role_required:
            # Match the entire function definition
            pattern = r'def role_required\([^)]*\):.*?return decorator\n'
            content = re.sub(pattern, '', content, flags=re.DOTALL)
            needs_update = True
        
        # Remove _get_decimal definition
        if has_get_decimal:
            pattern = r'def _get_decimal\([^)]*\):.*?return Decimal\(fallback\)\n'
            content = re.sub(pattern, '', content, flags=re.DOTALL)
            needs_update = True
        
        # Remove _paginate_query definition
        if has_paginate:
            pattern = r'def _paginate_query\([^)]*\):.*?return db\.paginate\([^)]*\)\n'
            content = re.sub(pattern, '', content, flags=re.DOTALL)
            needs_update = True
        
        # Remove _parse_date definition
        if has_parse_date:
            pattern = r'def _parse_date\([^)]*\):.*?return (fallback|None|date\.today\(\))\n'
            content = re.sub(pattern, '', content, flags=re.DOTALL)
            needs_update = True
        
        # Remove allowed_file definition
        if has_allowed_file:
            pattern = r'def allowed_file\([^)]*\):.*?return .*?\n'
            content = re.sub(pattern, '', content, flags=re.DOTALL)
            needs_update = True
        
        # Add import from utils if needed
        imports_needed = []
        if has_role_required:
            imports_needed.append('role_required')
        if has_get_decimal:
            imports_needed.append('_get_decimal')
        if has_paginate:
            imports_needed.append('_paginate_query')
        if has_parse_date:
            imports_needed.append('_parse_date')
        if has_allowed_file:
            imports_needed.append('allowed_file')
        
        if imports_needed and 'from utils import' not in content:
            # Find the last import statement
            import_pattern = r'(from [\w.]+ import [^\n]+)'
            imports = list(re.finditer(import_pattern, content))
            if imports:
                last_import = imports[-1]
                insert_pos = last_import.end()
                import_line = f"\nfrom utils import {', '.join(imports_needed)}"
                content = content[:insert_pos] + import_line + content[insert_pos:]
            else:
                # No imports found, add at the beginning after module docstring
                content = f"from utils import {', '.join(imports_needed)}\n{content}"
            needs_update = True
        
        # Remove unused imports
        if 'from functools import wraps' in content:
            # Check if wraps is still used
            if 'wraps(' not in content:
                content = re.sub(r'from functools import wraps\n', '', content)
                content = re.sub(r'from functools import wraps, ', 'from functools import ', content)
                content = re.sub(r', wraps', '', content)
                needs_update = True
        
        if needs_update and content != original_content:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)
            return True
        
        return False
    except Exception as e:
        print(f"Error updating {filepath}: {e}")
        return False

if __name__ == '__main__':
    # This is a helper script - manual updates are safer for complex refactoring
    print("This script is a helper. Manual updates are recommended for safety.")
    print("Use this as a reference for the update pattern.")

