# SAS Management System Auto-Updater

## Overview
The auto-update system checks for new versions and installs them automatically without user intervention.

## Components

### 1. updater.py
- Checks remote JSON file at: `https://sas-best-foods-updates.com/update.json`
- Compares local version (1.0) with server version
- Downloads and runs installer if newer version exists
- Closes the app automatically during update

### 2. app.py Integration
- Imports updater on startup
- Runs `updater.check_for_updates()` in background thread
- UI loads instantly (non-blocking)

### 3. SAS_Installer.iss
- Includes updater.exe in installation
- Runs updater.exe silently after installation

## Setup Instructions

### Step 1: Build updater.exe
```powershell
.\build_updater_exe.ps1
```

This will create `dist\updater.exe` using PyInstaller.

### Step 2: Rebuild Installer
After building updater.exe, rebuild your installer:
```powershell
.\build_installer_now.ps1
```

The installer will now include updater.exe.

### Step 3: Update Server JSON
Create/update the JSON file at `https://sas-best-foods-updates.com/update.json`:

```json
{
  "version": "1.1",
  "download_url": "https://sas-best-foods-updates.com/downloads/SAS_Installer.exe",
  "release_notes": "Bug fixes and improvements"
}
```

## How It Works

1. **On App Startup**: 
   - App loads normally
   - Background thread checks for updates (waits 5 seconds)

2. **Update Check**:
   - Fetches update.json from server
   - Compares versions
   - If newer version exists, downloads installer

3. **Update Installation**:
   - Downloads SAS_Installer.exe to app directory
   - Runs installer silently (/VERYSILENT)
   - Closes current app
   - Installer updates the application

4. **After Installation**:
   - Updater runs silently (from [Run] section)
   - Checks for updates again
   - Process repeats

## Version Management

Update `CURRENT_VERSION` in `updater.py` when releasing new versions:
```python
CURRENT_VERSION = "1.0"  # Change to "1.1", "1.2", etc.
```

## Testing

To test the updater:
1. Set up a test update.json with version > 1.0
2. Run the app
3. Check console/logs for update messages
4. Verify installer downloads and runs

## Notes

- Updater runs in background - doesn't block UI
- Silent installation - no user prompts
- Automatic app closure during update
- Desktop shortcut preserved
- Existing installer logic untouched

