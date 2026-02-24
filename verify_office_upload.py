#!/usr/bin/env python
"""Verify Office File Upload Implementation"""
import sys
import os

# Add the sas_management directory to path
sys.path.insert(0, 'sas_management')

try:
    from sas_management.app import create_app
    
    print("=" * 60)
    print("OFFICE FILE UPLOAD VERIFICATION")
    print("=" * 60)
    
    # Create app
    app = create_app()
    
    # Get all office routes
    office_routes = []
    for rule in app.url_map.iter_rules():
        if 'office' in rule.rule.lower():
            office_routes.append({
                'rule': rule.rule,
                'methods': sorted(rule.methods - {'HEAD', 'OPTIONS'}),
                'endpoint': rule.endpoint
            })
    
    print(f"\n✓ Found {len(office_routes)} office route(s):\n")
    for route in sorted(office_routes, key=lambda x: x['rule']):
        methods = ', '.join(route['methods'])
        print(f"  {route['rule']:<40} [{methods}]")
    
    # Check for upload route specifically
    upload_route = next((r for r in office_routes if '/file/upload' in r['rule']), None)
    if upload_route:
        print(f"\n✓ Upload route found: {upload_route['rule']}")
        print(f"  Methods: {', '.join(upload_route['methods'])}")
    else:
        print("\n✗ Upload route NOT FOUND!")
    
    # Check directory structure
    instance_path = app.instance_path
    office_uploads_dir = os.path.join(instance_path, 'office_uploads')
    
    print(f"\n✓ Instance path: {instance_path}")
    print(f"✓ Office uploads directory: {office_uploads_dir}")
    
    if os.path.exists(office_uploads_dir):
        print(f"  ✓ Directory exists")
        subdirs = [d for d in os.listdir(office_uploads_dir) 
                  if os.path.isdir(os.path.join(office_uploads_dir, d))]
        if subdirs:
            print(f"  ✓ Subdirectories: {', '.join(subdirs)}")
        else:
            print(f"  ℹ No subdirectories yet (will be created on first upload)")
    else:
        print(f"  ✗ Directory does NOT exist")
    
    # Check database model
    from sas_management.models import OfficeFile, OfficeFolder
    print(f"\n✓ Database models found:")
    print(f"  - OfficeFile: {OfficeFile.__tablename__}")
    print(f"  - OfficeFolder: {OfficeFolder.__tablename__}")
    
    # Test import of upload function
    from sas_management.blueprints.office import office_bp
    print(f"\n✓ Office blueprint imported successfully")
    print(f"  Blueprint name: {office_bp.name}")
    print(f"  URL prefix: {office_bp.url_prefix}")
    
    print("\n" + "=" * 60)
    print("VERIFICATION COMPLETE")
    print("=" * 60)
    
except Exception as e:
    print(f"\n✗ ERROR: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
