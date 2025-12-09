#!/usr/bin/env python3
"""
Duplicate Detection Script for SAS Management System
Finds duplicate functions, decorators, and code patterns across the codebase.
"""

import os
import re
from collections import defaultdict
from pathlib import Path

# Patterns to search for
PATTERNS = {
    'role_required': r'^def role_required\(',
    '_get_decimal': r'^def _get_decimal\(',
    '_paginate_query': r'^def _paginate_query\(',
    '_parse_date': r'^def _parse_date\(',
    'allowed_file': r'^def allowed_file\(',
}

# Route patterns
ROUTE_PATTERN = r'@.*\.route\(["\']([^"\']+)["\']'

def find_duplicates():
    """Find duplicate code patterns in the codebase."""
    results = defaultdict(list)
    route_paths = defaultdict(list)
    
    # Walk through Python files
    for root, dirs, files in os.walk('.'):
        # Skip common directories
        if any(skip in root for skip in ['__pycache__', '.git', 'instance', 'venv', 'env']):
            continue
            
        for file in files:
            if not file.endswith('.py'):
                continue
                
            filepath = os.path.join(root, file)
            rel_path = os.path.relpath(filepath)
            
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    lines = f.readlines()
                    
                    # Check for duplicate patterns
                    for pattern_name, pattern in PATTERNS.items():
                        for line_num, line in enumerate(lines, 1):
                            if re.search(pattern, line):
                                results[pattern_name].append({
                                    'file': rel_path,
                                    'line': line_num,
                                    'code': line.strip()
                                })
                    
                    # Check for duplicate routes
                    for line_num, line in enumerate(lines, 1):
                        route_match = re.search(ROUTE_PATTERN, line)
                        if route_match:
                            route_path = route_match.group(1)
                            route_paths[route_path].append({
                                'file': rel_path,
                                'line': line_num,
                                'code': line.strip()
                            })
                            
            except Exception as e:
                print(f"Error reading {filepath}: {e}")
    
    return results, route_paths

def print_results(results, route_paths):
    """Print duplicate detection results."""
    print("=" * 80)
    print("DUPLICATE CODE DETECTION REPORT")
    print("=" * 80)
    print()
    
    # Print function duplicates
    for pattern_name, occurrences in results.items():
        if len(occurrences) > 1:
            print(f"\n🔴 {pattern_name.upper()} - Found {len(occurrences)} instances:")
            print("-" * 80)
            for occ in occurrences:
                print(f"  {occ['file']}:{occ['line']}")
                print(f"    {occ['code']}")
            print()
    
    # Print route duplicates
    print("\n" + "=" * 80)
    print("DUPLICATE ROUTES")
    print("=" * 80)
    print()
    
    duplicate_routes = {path: occs for path, occs in route_paths.items() if len(occs) > 1}
    
    if duplicate_routes:
        for route_path, occurrences in duplicate_routes.items():
            print(f"\n⚠️  Route '{route_path}' defined {len(occurrences)} times:")
            for occ in occurrences:
                print(f"  {occ['file']}:{occ['line']}")
    else:
        print("✅ No duplicate routes found")
    
    # Summary
    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print()
    
    total_duplicates = sum(len(occs) for occs in results.values() if len(occs) > 1)
    print(f"Total duplicate functions found: {total_duplicates}")
    print(f"Duplicate routes found: {len(duplicate_routes)}")
    
    print("\n📋 Recommendations:")
    print("  1. Consolidate role_required decorator into utils/decorators.py")
    print("  2. Consolidate helper functions into utils/helpers.py")
    print("  3. Review duplicate routes for conflicts")

if __name__ == '__main__':
    print("Scanning codebase for duplicates...")
    results, route_paths = find_duplicates()
    print_results(results, route_paths)

