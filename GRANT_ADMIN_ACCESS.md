# Grant Full Admin Access

This guide explains how to grant yourself full admin access to the system.

## Method 1: Automatic (First User)

The system automatically grants admin access to the **first user** (user ID = 1) in the database. If you're the first user created, you already have full admin access!

## Method 2: Using the Script

Run the provided script to grant SuperAdmin role to your account:

```bash
python grant_admin_access.py your-email@example.com
```

Replace `your-email@example.com` with your actual email address.

If you don't specify an email, the script will:
- Show all available users
- Use the first user in the database

## Method 3: Hardcode Your Email (Permanent Access)

Edit `models.py` and add your email to the `ADMIN_EMAILS` list in the `is_super_admin()` method:

```python
ADMIN_EMAILS = [
    "your-email@example.com",  # Add your email here
]
```

This will grant you permanent admin access regardless of your role assignment.

## Method 4: Through Admin Panel

If you already have some admin access:
1. Log in to the system
2. Go to `/admin/users`
3. Find your user account
4. Edit your user
5. Assign the "SuperAdmin" role

## What Admin Access Gives You

With SuperAdmin access, you can:
- ✅ Access all system features
- ✅ Bypass all permission checks
- ✅ Manage users, roles, and permissions
- ✅ Access the admin dashboard
- ✅ Perform all administrative tasks

## Verification

After granting access, you can verify by:
1. Logging out and logging back in
2. Checking if you can access `/admin/dashboard`
3. Looking for the "SUPER ADMIN MODE" badge at the top of the page

## Troubleshooting

If you still don't have access:
1. Make sure you logged out and logged back in
2. Check that the SuperAdmin role exists: `/admin/roles`
3. Verify your user has the SuperAdmin role assigned
4. Check the browser console for any errors

