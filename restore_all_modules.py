#!/usr/bin/env python3
"""
Comprehensive Module Restoration Script
Restores all modules including SAS AI with sample data.
"""
import os
import sys
from datetime import datetime, date, timedelta
from decimal import Decimal

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from sas_management.app import create_app
from sas_management.models import db, User, Role, UserRole

def restore_all_modules():
    """Restore all modules with sample data."""
    app = create_app()
    
    with app.app_context():
        print("=" * 70)
        print("SAS MANAGEMENT SYSTEM - COMPREHENSIVE MODULE RESTORATION")
        print("=" * 70)
        print()
        
        # Ensure admin user exists
        print("[1/10] Ensuring admin user exists...")
        admin_user = User.query.filter_by(email="admin@sas.com").first()
        if not admin_user:
            from werkzeug.security import generate_password_hash
            admin_user = User(
                email="admin@sas.com",
                username="admin",
                password_hash=generate_password_hash("admin123"),
                role=UserRole.Admin,
                is_admin=True,
                first_login=False,
                must_change_password=False
            )
            db.session.add(admin_user)
            db.session.commit()
            print("  ✓ Created admin user: admin@sas.com / admin123")
        else:
            print("  ✓ Admin user already exists")
        
        # Ensure roles exist
        print("\n[2/10] Ensuring roles exist...")
        try:
            from sas_management.utils.role_utils import ensure_roles_exist
            roles_created = ensure_roles_exist()
            if roles_created > 0:
                print(f"  ✓ Created {roles_created} roles")
            else:
                print("  ✓ All roles already exist")
        except Exception as e:
            print(f"  ⚠️  Error ensuring roles: {e}")
        
        # Seed RBAC
        print("\n[3/10] Seeding RBAC system...")
        try:
            from seed_rbac_complete import seed_rbac_complete
            seed_rbac_complete()
            print("  ✓ RBAC system seeded")
        except Exception as e:
            print(f"  ⚠️  Error seeding RBAC: {e}")
        
        # Seed AI features
        print("\n[4/10] Seeding SAS AI features...")
        try:
            from sas_management.ai.models import ensure_default_ai_features
            ensure_default_ai_features()
            print("  ✓ SAS AI features enabled")
        except Exception as e:
            print(f"  ⚠️  Error seeding AI features: {e}")
        
        # Seed AI sample data
        print("\n[5/10] Seeding AI sample data...")
        try:
            from seed_ai_sample_data import seed_ai_data
            seed_ai_data()
            print("  ✓ AI sample data seeded")
        except Exception as e:
            print(f"  ⚠️  Error seeding AI data: {e}")
        
        # Seed CRM/Pipeline data
        print("\n[6/10] Seeding CRM and Pipeline data...")
        try:
            from seed_crm_pipeline_data import seed_pipeline_data
            seed_pipeline_data()
            print("  ✓ CRM/Pipeline data seeded")
        except Exception as e:
            print(f"  ⚠️  Error seeding CRM data: {e}")
        
        # Seed Enterprise modules
        print("\n[7/10] Seeding Enterprise modules...")
        try:
            from seed_enterprise_modules import seed_enterprise_data
            seed_enterprise_data()
            print("  ✓ Enterprise modules seeded")
        except Exception as e:
            print(f"  ⚠️  Error seeding enterprise modules: {e}")
        
        # Seed Premium modules
        print("\n[8/10] Seeding Premium modules...")
        try:
            from seed_premium_modules import seed_premium_modules
            seed_premium_modules()
            print("  ✓ Premium modules seeded")
        except Exception as e:
            print(f"  ⚠️  Error seeding premium modules: {e}")
        
        # Seed Production data
        print("\n[9/10] Seeding Production data...")
        try:
            from seed_production_quality_control_data import seed_production_qc_data
            seed_production_qc_data()
            print("  ✓ Production data seeded")
        except Exception as e:
            print(f"  ⚠️  Error seeding production data: {e}")
        
        # Seed HR data
        print("\n[10/10] Seeding HR data...")
        try:
            from seed_hr_sample_data import seed_hr_data
            seed_hr_data()
            print("  ✓ HR data seeded")
        except Exception as e:
            print(f"  ⚠️  Error seeding HR data: {e}")
        
        print("\n" + "=" * 70)
        print("RESTORATION COMPLETE!")
        print("=" * 70)
        print("\nAll modules have been restored with sample data.")
        print("SAS AI features are enabled and ready to use.")
        print("\nLogin credentials:")
        print("  Email: admin@sas.com")
        print("  Password: admin123")
        print("\nAccess the dashboard at: http://127.0.0.1:5000/dashboard")
        print()

if __name__ == "__main__":
    restore_all_modules()
