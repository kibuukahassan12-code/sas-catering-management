"""
SAS Management System Auto-Updater
Checks for updates and installs them automatically
"""
import os
import sys
import json
import urllib.request
import urllib.error
import subprocess
import threading
import time
from pathlib import Path

# Current version - update this when releasing new versions
CURRENT_VERSION = "1.0"

# Update server URL
UPDATE_URL = "https://sas-best-foods-updates.com/update.json"

# Local paths
APP_DIR = Path(os.path.dirname(os.path.abspath(sys.executable if getattr(sys, 'frozen', False) else __file__)))
INSTALLER_NAME = "SAS_Installer.exe"
INSTALLER_PATH = APP_DIR / INSTALLER_NAME


def get_local_version():
    """Get the current local version"""
    return CURRENT_VERSION


def check_server_version():
    """Check the server for the latest version"""
    try:
        with urllib.request.urlopen(UPDATE_URL, timeout=10) as response:
            data = json.loads(response.read().decode())
            return {
                'version': data.get('version', '1.0'),
                'download_url': data.get('download_url', ''),
                'release_notes': data.get('release_notes', '')
            }
    except (urllib.error.URLError, urllib.error.HTTPError, json.JSONDecodeError, Exception) as e:
        print(f"Update check failed: {e}")
        return None


def download_installer(download_url):
    """Download the installer from the server"""
    try:
        print(f"Downloading update from {download_url}...")
        urllib.request.urlretrieve(download_url, INSTALLER_PATH)
        print(f"Download complete: {INSTALLER_PATH}")
        return True
    except Exception as e:
        print(f"Download failed: {e}")
        return False


def run_installer_silently():
    """Run the installer silently and close the app"""
    try:
        if not INSTALLER_PATH.exists():
            print(f"Installer not found: {INSTALLER_PATH}")
            return False
        
        print("Running installer silently...")
        # Run installer silently: /S = silent, /SILENT = silent, /VERYSILENT = very silent
        subprocess.Popen([
            str(INSTALLER_PATH),
            "/VERYSILENT",
            "/NORESTART",
            "/SUPPRESSMSGBOXES"
        ], shell=False)
        
        # Wait a moment for installer to start
        time.sleep(2)
        
        # Close the current application
        print("Closing application for update...")
        os._exit(0)
        
        return True
    except Exception as e:
        print(f"Failed to run installer: {e}")
        return False


def check_for_updates():
    """Main function to check for updates"""
    try:
        print("Checking for updates...")
        server_info = check_server_version()
        
        if not server_info:
            print("Could not check for updates. Continuing with current version.")
            return False
        
        server_version = server_info['version']
        local_version = get_local_version()
        
        print(f"Local version: {local_version}")
        print(f"Server version: {server_version}")
        
        # Compare versions (simple string comparison - can be improved)
        if server_version > local_version:
            print(f"New version available: {server_version}")
            
            download_url = server_info['download_url']
            if not download_url:
                print("No download URL provided in update info.")
                return False
            
            # Download installer
            if download_installer(download_url):
                # Run installer and close app
                return run_installer_silently()
        else:
            print("Application is up to date.")
            return False
            
    except Exception as e:
        print(f"Update check error: {e}")
        return False


def check_for_updates_background():
    """Run update check in background thread"""
    def run_check():
        # Wait a few seconds after app starts before checking
        time.sleep(5)
        check_for_updates()
    
    thread = threading.Thread(target=run_check, daemon=True)
    thread.start()


if __name__ == "__main__":
    # If run directly, check for updates immediately
    check_for_updates()

