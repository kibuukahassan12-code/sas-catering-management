"""Utility functions for role management."""
from datetime import datetime
from sas_management.models import db, User, Role


def check_expired_roles():
    """Check and revert expired temporary role assignments."""
    try:
        now = datetime.utcnow()
        expired_users = User.query.filter(
            User.is_temporary_role == True,
            User.role_expiry_date.isnot(None),
            User.role_expiry_date < now
        ).all()
        
        reverted_count = 0
        for user in expired_users:
            # Restore previous role
            if user.previous_role_id:
                user.role_id = user.previous_role_id
                user.previous_role_id = None
                user.is_temporary_role = False
                user.role_expiry_date = None
                user.role_expires_at = None
                reverted_count += 1
            else:
                # No previous role, just clear temporary assignment
                user.is_temporary_role = False
                user.role_expiry_date = None
                user.role_expires_at = None
        
        if reverted_count > 0:
            db.session.commit()
            return reverted_count
        
        return 0
    except Exception as e:
        db.session.rollback()
        from flask import current_app
        if current_app:
            current_app.logger.error(f"Error checking expired roles: {e}")
        return 0


def ensure_roles_exist():
    """Ensure all required system roles exist in the database."""
    required_roles = [
        {"name": "ADMIN", "description": "System – Full Access", "is_system_role": True, "system_protected": True},
        {"name": "Manager", "description": "Manager role with elevated permissions", "is_system_role": False, "system_protected": False},
        {"name": "HR", "description": "Human Resources role", "is_system_role": False, "system_protected": False},
        {"name": "Accounting", "description": "Accounting department role", "is_system_role": False, "system_protected": False},
        {"name": "Event Service", "description": "Event service management role", "is_system_role": False, "system_protected": False},
        {"name": "Inventory", "description": "Inventory / Store management role", "is_system_role": False, "system_protected": False},
        {"name": "Kitchen", "description": "Kitchen staff role", "is_system_role": False, "system_protected": False},
        {"name": "Sales", "description": "Sales department role", "is_system_role": False, "system_protected": False},
        {"name": "Staff", "description": "General staff role", "is_system_role": False, "system_protected": False},
        {"name": "Read-Only", "description": "Read-only access role", "is_system_role": False, "system_protected": False},
        {"name": "Client Portal User", "description": "Client portal access role", "is_system_role": False, "system_protected": False},
        {"name": "SAS AI Analyst", "description": "SAS AI Analyst role", "is_system_role": False, "system_protected": False},
    ]
    
    created_count = 0
    for role_data in required_roles:
        existing_role = Role.query.filter_by(name=role_data["name"]).first()
        if not existing_role:
            role = Role(
                name=role_data["name"],
                description=role_data["description"],
                is_system_role=role_data["is_system_role"],
                system_protected=role_data["system_protected"]
            )
            db.session.add(role)
            created_count += 1
        else:
            # Update system_protected flag for ADMIN role if missing
            if role_data["name"] == "ADMIN" and not existing_role.system_protected:
                existing_role.system_protected = True
                existing_role.is_system_role = True
                created_count += 0  # Don't count updates
    
    if created_count > 0:
        db.session.commit()
    
    return created_count

