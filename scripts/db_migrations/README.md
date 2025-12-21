# Database Migrations

This directory contains manual migration scripts for database schema updates.

## Event Service Department Migration

### `fix_service_events_schema.py`

Safely synchronizes the `service_events` table and related tables with the authoritative ServiceEvent model definition.

**Usage:**
```bash
python scripts/db_migrations/fix_service_events_schema.py
```

**What it does:**
- Checks existing columns in `service_events` table
- Adds only missing columns (never drops or renames)
- Creates supporting tables if they don't exist:
  - `service_event_items`
  - `service_staff_assignments`
  - `service_checklist_items`
- Uses SQLite-safe ALTER TABLE statements
- Logs each action clearly

**Safety:**
- Never drops columns
- Never renames columns
- Only adds missing columns
- Handles duplicate column errors gracefully
- Rolls back on errors

**When to run:**
- After deploying new ServiceEvent model changes
- When you see "no such column: service_events.title" errors
- Before first use of Event Service module
- After database restore from backup

**Note:** This migration is excluded from the auto-fix system. It must be run manually.

