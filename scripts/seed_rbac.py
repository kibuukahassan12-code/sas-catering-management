"""
RBAC Seed Script - Safely create core permissions and assign them to the Admin role.

Usage:
    python scripts/seed_rbac.py
"""

from typing import Dict, List, Tuple

from sas_management.app import create_app
from sas_management.models import db, Permission, Role, RolePermission


# group -> list of (code_suffix, display_name, description)
PERMISSIONS_DEFINITION: Dict[str, List[Tuple[str, str, str]]] = {
    "admin": [
        ("manage_users", "Manage Users", "Can create, edit, and disable users."),
        ("manage_roles", "Manage Roles", "Can create, edit, and manage roles."),
        ("manage_permissions", "Manage Permissions", "Can manage system permissions."),
        ("view_audit_logs", "View Audit Logs", "Can view system audit and activity logs."),
        ("system_settings", "System Settings", "Can configure global system settings."),
    ],
    "hr": [
        ("view_hr", "View HR", "Can view HR records and staff profiles."),
        ("create_hr", "Create HR Records", "Can create new HR records."),
        ("edit_hr", "Edit HR Records", "Can edit existing HR records."),
        ("delete_hr", "Delete HR Records", "Can delete HR records."),
    ],
    "accounting": [
        ("view_accounting", "View Accounting", "Can view accounting data and ledgers."),
        ("create_invoice", "Create Invoice", "Can create new invoices."),
        ("approve_payments", "Approve Payments", "Can approve outgoing payments."),
        ("view_reports", "View Financial Reports", "Can view financial reports and analytics."),
    ],
    "event_service": [
        ("view_events", "View Events", "Can view events and event details."),
        ("create_events", "Create Events", "Can create new events."),
        ("edit_events", "Edit Events", "Can edit existing events."),
        ("approve_events", "Approve Events", "Can approve events for execution."),
    ],
    "inventory": [
        ("view_inventory", "View Inventory", "Can view inventory levels and items."),
        ("create_inventory", "Create Inventory Records", "Can add new inventory items or batches."),
        ("edit_inventory", "Edit Inventory", "Can edit existing inventory records."),
        ("delete_inventory", "Delete Inventory", "Can delete or archive inventory records."),
    ],
    "bakery": [
        ("view_bakery_orders", "View Bakery Orders", "Can view bakery orders and their status."),
        ("create_bakery_orders", "Create Bakery Orders", "Can create new bakery orders."),
        ("edit_bakery_orders", "Edit Bakery Orders", "Can edit existing bakery orders."),
        ("delete_bakery_orders", "Delete Bakery Orders", "Can cancel or delete bakery orders."),
    ],
    "sas_ai": [
        ("access_ai_chat", "Access AI Chat", "Can access SAS AI chat assistants."),
        ("access_ai_reports", "Access AI Reports", "Can access AI-generated reports and insights."),
        ("manage_ai_features", "Manage AI Features", "Can enable, disable, or configure AI features."),
    ],
}


def seed_rbac() -> None:
    """Seed required permissions and ensure Admin has all of them."""
    app = create_app()

    with app.app_context():
        print("Seeding RBAC permissions...")

        created_count = 0
        updated_count = 0

        # Step 1: Create / update permissions
        for group_name, perms in PERMISSIONS_DEFINITION.items():
            for code_suffix, display_name, description in perms:
                full_code = f"{group_name}.{code_suffix}"

                # Try to find by code first (canonical), then by name as fallback
                permission = Permission.query.filter(
                    (Permission.code == full_code) | (Permission.name == display_name)
                ).first()

                if not permission:
                    permission = Permission(
                        code=full_code,
                        name=display_name,
                        group=group_name,
                        module=group_name,
                        action=code_suffix,
                        description=description,
                    )
                    db.session.add(permission)
                    created_count += 1
                    print(f"  [CREATED] {full_code} ({display_name})")
                else:
                    # Update missing metadata without changing identity
                    changed = False
                    if not permission.group:
                        permission.group = group_name
                        changed = True
                    if not permission.module:
                        permission.module = group_name
                        changed = True
                    if not permission.action:
                        permission.action = code_suffix
                        changed = True
                    if not permission.description:
                        permission.description = description
                        changed = True
                    if changed:
                        updated_count += 1
                        print(f"  [UPDATED] metadata for {full_code}")

        db.session.commit()
        total_permissions = Permission.query.count()
        print(f"\nPermissions seeding complete.")
        print(f"   - Created: {created_count}")
        print(f"   - Updated: {updated_count}")
        print(f"   - Total in database: {total_permissions}")

        # Step 2: Ensure Admin role exists
        admin_role = Role.query.filter(Role.name.in_(["Admin", "ADMIN"])).first()
        if not admin_role:
            print("WARNING: Admin role not found (name 'Admin' or 'ADMIN'). No role-permission links were changed.")
            return

        # Step 3: Assign ALL permissions to Admin (without removing existing ones)
        print("\nAssigning all permissions to Admin role...")
        all_permissions = Permission.query.all()
        added_links = 0

        for perm in all_permissions:
            existing_link = RolePermission.query.filter_by(
                role_id=admin_role.id,
                permission_id=perm.id,
            ).first()
            if not existing_link:
                rp = RolePermission(role_id=admin_role.id, permission_id=perm.id)
                db.session.add(rp)
                added_links += 1

        db.session.commit()
        print(f"   - New role-permission links added for Admin: {added_links}")
        print("   - Admin now has full access to all permissions.")


if __name__ == "__main__":
    seed_rbac()


