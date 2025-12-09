# RBAC Setup Guide

## Quick Start

### Step 1: Run Database Migration
```bash
python migrate_rbac.py
```

This will:
- Create `roles` table
- Create `permissions` table  
- Create `role_permissions` junction table
- Add `role_id` column to `user` table
- Add `force_password_change` column to `user` table

### Step 2: Seed Default Roles and Permissions
```bash
python seed_rbac.py
```

This will:
- Create all default permissions (dashboard.view, orders.create, etc.)
- Create default roles (Super Admin, Manager, Chef, etc.)
- Assign permissions to roles
- Assign Super Admin role to existing Admin users

### Step 3: Access Admin Panel
1. Log in as an Admin user (they should have Super Admin role)
2. Navigate to `/admin/roles` to manage roles
3. Navigate to `/admin/user-roles` to assign roles to users
4. Navigate to `/admin/permissions` to view all permissions

## Permission Format

Permissions use the format: `module.action`

Examples:
- `dashboard.view` - View dashboard
- `orders.create` - Create orders
- `orders.edit` - Edit orders
- `orders.delete` - Delete orders
- `events.manage` - Full event management
- `events.view` - View events only
- `admin.manage` - System administration

## Using Permissions in Routes

### Basic Usage
```python
from utils import require_permission

@blueprint.route("/example")
@login_required
@require_permission("module.action")
def example_route():
    return render_template("example.html")
```

### Multiple Permissions (OR logic)
```python
# User needs EITHER permission
@require_permission("orders.create")
@require_permission("orders.edit")
def edit_or_create():
    pass
```

### In Templates
```jinja2
{% if current_user.has_permission("orders.create") %}
    <a href="{{ url_for('orders.create') }}">Create Order</a>
{% endif %}
```

## Default Roles

### Super Admin
- **Description**: Full system access
- **Permissions**: All permissions automatically granted
- **Use Case**: System administrators

### Manager
- **Description**: Management role with broad access
- **Permissions**: 
  - dashboard.view
  - orders.create, orders.edit, orders.view
  - events.manage, events.view
  - staff.manage, staff.view
  - finance.view
  - inventory.view
  - production.view
  - communication.access

### Chef
- **Description**: Kitchen and production management
- **Permissions**:
  - dashboard.view
  - orders.view
  - events.view
  - inventory.manage, inventory.view
  - production.manage, production.view

### Waiter
- **Description**: Service staff with limited access
- **Permissions**:
  - dashboard.view
  - orders.view
  - events.view
  - staff.view

### Accountant
- **Description**: Financial operations and reporting
- **Permissions**:
  - dashboard.view
  - orders.view
  - finance.view, finance.manage

### Store Manager
- **Description**: Inventory and store management
- **Permissions**:
  - dashboard.view
  - orders.view, orders.create, orders.edit
  - inventory.manage, inventory.view
  - production.view

### Basic Staff
- **Description**: Basic staff with minimal access
- **Permissions**:
  - dashboard.view
  - orders.view

## Managing Roles

### Create a New Role
1. Go to `/admin/roles`
2. Click "Create Role"
3. Enter role name and description
4. Select permissions for the role
5. Save

### Edit a Role
1. Go to `/admin/roles`
2. Click "Edit" on the role
3. Modify name, description, or permissions
4. Save

### Assign Role to User
1. Go to `/admin/user-roles`
2. Find the user
3. Select a role from the dropdown
4. Click "Assign"

## Troubleshooting

### Permission Denied Errors
- Check if user has the required role
- Verify role has the required permission
- Check route decorator is using correct permission name

### Menu Items Not Showing
- Verify user has permission for the module
- Check `templates/base.html` permission checks
- Verify `routes.py` module filtering logic

### Super Admin Not Working
- Ensure user has `role_id` pointing to Super Admin role
- Check `Role.has_permission()` method returns True for Super Admin
- Verify role name is exactly "Super Admin"

## Migration Notes

- Old `role` table is renamed to `role_old` (backup)
- Old `permission` table is renamed to `permission_old` (backup)
- Existing users keep their legacy `role` enum value
- Admin users are automatically assigned Super Admin role

## API Reference

### Models
- `Role` - Role model with `has_permission(name)` method
- `Permission` - Permission model with module.action format
- `RolePermission` - Junction table model
- `User` - Updated with `has_permission(name)` method

### Decorators
- `@require_permission("module.action")` - Route protection
- `@permission_required("module")` - Legacy module-level protection (backward compatible)

### Helper Functions
- `has_permission(permission_name)` - Check if current user has permission
- `current_user.has_permission(permission_name)` - User instance method

## Next Steps

1. Review and update remaining routes with `@require_permission` decorator
2. Update menu generation in `routes.py` to use new permission format
3. Test all permission checks
4. Document any custom permissions added

