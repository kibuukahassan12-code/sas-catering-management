#!/usr/bin/env python3
"""Check available login credentials."""
import os
os.environ["SECRET_KEY"] = "sas-management-system-secret-key-2024-production"

from sas_management.app import create_app
from sas_management.models import db, User

app = create_app()
with app.app_context():
    print("=" * 70)
    print("SAS MANAGEMENT SYSTEM - LOGIN CREDENTIALS")
    print("=" * 70)
    print()
    
    # Check admin user
    admin = User.query.filter_by(email="admin@sas.com").first()
    if admin:
        print("ADMIN USER:")
        print(f"  Email: admin@sas.com")
        print(f"  Username: {admin.username or 'N/A'}")
        print(f"  Role: {admin.role}")
        print()
        print("PASSWORD OPTIONS (try these in order):")
        print("  1. password (default)")
        print("  2. admin123 (if reset)")
        print()
        # Test passwords
        if admin.check_password("password"):
            print("  [CONFIRMED] Password 'password' works!")
        elif admin.check_password("admin123"):
            print("  [CONFIRMED] Password 'admin123' works!")
        else:
            print("  [WARNING] Neither password works - password may need reset")
    else:
        print("  [ERROR] Admin user not found!")
        print("  Run: python quick_seed.py to create admin user")
    
    print()
    print("ALL USERS IN SYSTEM:")
    print("-" * 70)
    users = User.query.all()
    if users:
        for user in users:
            print(f"  Email: {user.email}")
            print(f"  Username: {user.username or 'N/A'}")
            print(f"  Role: {user.role}")
            print()
    else:
        print("  No users found in database")
    
    print("=" * 70)
