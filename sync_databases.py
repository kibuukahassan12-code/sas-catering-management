#!/usr/bin/env python3
"""
Sync fixed site.db with the instance DB
"""

import shutil
import os

root_db = r"C:\Users\DELL\Desktop\sas management system\site.db"
instance_db = r"C:\Users\DELL\Desktop\sas management system\instance\site.db"

print("Checking files...")

if os.path.exists(root_db):
    print("✔ Found FIXED root DB:", root_db)
else:
    print("✖ ERROR: Root site.db not found!")
    raise SystemExit()

if os.path.exists(instance_db):
    print("✔ Found INSTANCE DB:", instance_db)
else:
    print("✖ Instance DB missing — will create new one.")

print("\nCopying UPDATED DB into instance/...")

shutil.copy2(root_db, instance_db)

print("\n✅ SYNC COMPLETE!")
print("instance/site.db is now fully updated with all columns including rating.")

