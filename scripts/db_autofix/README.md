# Database Auto-Fix System

## Overview
This system automatically detects and adds missing columns to database tables to match SQLAlchemy models. It runs on every server startup to ensure database schema is always synchronized with model definitions.

## How It Works

1. **Automatic Detection**: Scans all SQLAlchemy models in `sas_management.models`
2. **Column Comparison**: Compares model columns with actual database columns
3. **Auto-Fix**: Adds any missing columns with correct data types
4. **Error Prevention**: Prevents "no such column" errors permanently

## Features

- ✅ Automatically checks ALL 136+ models
- ✅ Adds missing columns with correct SQLite types
- ✅ Handles DEFAULT values
- ✅ Safe error handling (skips duplicate columns)
- ✅ Runs automatically on server startup
- ✅ No manual migrations needed

## Files

- `scripts/db_autofix/auto_fix.py` - Main auto-fix system
- `scripts/db_autofix/__init__.py` - Package init file

## Integration

The system is integrated into `sas_management/app.py` and runs automatically before `db.create_all()`.

## Usage

The system runs automatically on server startup. To run manually:

```python
from scripts.db_autofix.auto_fix import auto_fix_schema
auto_fix_schema()
```

## Benefits

- **No Migration Conflicts**: Automatically handles schema changes
- **No Broken Pages**: Missing columns are added before they cause errors
- **Zero Maintenance**: Works automatically without manual intervention
- **Production Safe**: Handles errors gracefully, never breaks the app

