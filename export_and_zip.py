#!/usr/bin/env python
"""Script to export static HTML and create ZIP file for Netlify deployment."""
import os
import time
import zipfile
import requests
from pathlib import Path

# Wait for Flask to be ready
print("Waiting for Flask app to start...")
time.sleep(5)

# Try to trigger the export
try:
    print("Triggering export_static route...")
    response = requests.get("http://127.0.0.1:5000/university/export_static", timeout=15)
    print(f"Response status: {response.status_code}")
except requests.exceptions.RequestException as e:
    print(f"Could not connect to Flask app: {e}")
    print("Make sure Flask app is running on http://127.0.0.1:5000")
    exit(1)

# Check if static_site directory exists
static_site_dir = Path("sas_management/static_site")
if not static_site_dir.exists():
    print(f"Error: {static_site_dir} does not exist. Export may have failed.")
    exit(1)

# Check if index.html exists
index_file = static_site_dir / "index.html"
if not index_file.exists():
    print(f"Error: {index_file} does not exist. Export may have failed.")
    exit(1)

print(f"Found exported file: {index_file}")

# Create ZIP file
desktop_path = Path.home() / "Desktop"
zip_path = desktop_path / "saa_final_netlify.zip"

print(f"Creating ZIP file: {zip_path}")

with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
    # Add all files from static_site to root of ZIP
    for file_path in static_site_dir.rglob('*'):
        if file_path.is_file():
            # Add to root of ZIP (no folder structure)
            arcname = file_path.name
            zipf.write(file_path, arcname)
            print(f"  Added: {arcname}")

print(f"\n✓ ZIP file created successfully: {zip_path}")
print(f"✓ Ready to upload to Netlify!")

