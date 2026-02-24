#!/usr/bin/env python3
"""Ensure admin user exists with correct password."""
import os
os.environ["SECRET_KEY"] = "sas-management-system-secret-key-2024-production"

from sas_management.app import create_app
from sas_management.models import db, User, UserRole
from werkzeug.security import generate_password_hash

app = create_app()
with app.app_context():
    print("Ensuring admin user exists...")
    
    admin = User.query.filter_by(email="admin@sas.com").first()
    if not admin:
        print("Creating admin user...")
        admin = User(
            email="admin@sas.com",
            username="admin",
            role=UserRole.Admin,
            is_admin=True,
            first_login=False,
            must_change_password=False,
            force_password_change=False
        )
        admin.set_password("password")
        db.session.add(admin)
        db.session.commit()
        print("Admin user created!")
    else:
        print("Admin user exists, resetting password...")
        admin.set_password("password")
        admin.first_login = False
        admin.must_change_password = False
        admin.force_password_change = False
        admin.is_admin = True
        db.session.commit()
        print("Password reset to 'password'")
    
    # Verify
    test_user = User.query.filter_by(email="admin@sas.com").first()
    if test_user and test_user.check_password("password"):
        print("SUCCESS: Admin user verified!")
        print(f"Email: {test_user.email}")
        print(f"Password: password")
        print(f"Role: {test_user.role}")
    else:
        print("ERROR: Password verification failed!")
