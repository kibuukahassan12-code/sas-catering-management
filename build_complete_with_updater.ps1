$PY='C:\Users\DELL\AppData\Local\Programs\Python\Python312\python.exe'
$ISCC='C:\Program Files (x86)\Inno Setup 6\ISCC.exe'
$ROOT='C:\Users\DELL\Desktop\sas management system'

Set-Location $ROOT

Write-Host '1/7 Creating updater folder and python file...'
New-Item -Path (Join-Path $ROOT 'updater') -ItemType Directory -Force | Out-Null

$pyfile = Join-Path $ROOT 'updater\updater.py'

@'
import os, sys, urllib.request, tempfile, subprocess, json

# CONFIG: set your update metadata URL (must return JSON {"version":"1.0.1","installer_url":"https://example.com/SAS_Installer.exe"})
UPDATE_META_URL = "https://example.com/sas_update.json"
# Local version file relative to installed app folder (installer will place version.txt into {app})
LOCAL_VERSION_FILE = os.path.join(os.environ.get("PROGRAMFILES", r"C:\Program Files"), "SAS Management System", "version.txt")

def read_local_version():
    try:
        with open(LOCAL_VERSION_FILE,'r') as f:
            return f.read().strip()
    except Exception:
        return None

def fetch_update_meta():
    try:
        with urllib.request.urlopen(UPDATE_META_URL, timeout=10) as r:
            return json.loads(r.read().decode('utf-8'))
    except Exception:
        return None

def download_installer(url, dest):
    urllib.request.urlretrieve(url, dest)

def run_installer_silent(path):
    # Inno Setup installers support /VERYSILENT /SUPPRESSMSGBOXES /NORESTART
    subprocess.run([path, '/VERYSILENT', '/SUPPRESSMSGBOXES', '/NORESTART'], check=False)

def main():
    meta = fetch_update_meta()
    if not meta:
        sys.exit(0)  # nothing to do
    remote_ver = meta.get('version')
    installer_url = meta.get('installer_url')
    local_ver = read_local_version()
    if remote_ver and local_ver != remote_ver and installer_url:
        tf = tempfile.NamedTemporaryFile(delete=False, suffix='.exe')
        try:
            download_installer(installer_url, tf.name)
            run_installer_silent(tf.name)
        finally:
            try:
                os.unlink(tf.name)
            except Exception:
                pass

if __name__ == '__main__':
    main()
'@ | Out-File -FilePath $pyfile -Encoding UTF8 -Force

Write-Host '2/7 Installing PyInstaller and requests (user site)...'
& $PY -m pip install --user pyinstaller requests --upgrade | Out-Null
if ($LASTEXITCODE -ne 0) { Write-Error 'pip install failed'; exit 2 }

Write-Host '3/7 Building updater.exe with PyInstaller (onefile)...'
# use the Python interpreter to call PyInstaller. Use -m PyInstaller to avoid PATH issues.
& $PY -m PyInstaller --noconfirm --clean --onefile --name updater --distpath (Join-Path $ROOT 'installer') $pyfile
if ($LASTEXITCODE -ne 0) { Write-Error 'PyInstaller build failed'; exit 3 }

Write-Host '4/7 Verifying updater exists...'
if (-not (Test-Path (Join-Path $ROOT 'installer\updater.exe'))) { Write-Error 'updater.exe not found'; exit 4 }

Write-Host '5/7 Copying updater into installer payload (optional)...'
# (already built into installer folder via --distpath), ensure installer folder exists
New-Item -Path (Join-Path $ROOT 'installer') -ItemType Directory -Force | Out-Null
Copy-Item -Path (Join-Path $ROOT 'installer\updater.exe') -Destination (Join-Path $ROOT 'installer\updater.exe') -Force

Write-Host '6/7 Compiling Inno Setup script to build SAS_Installer.exe...'
$iss = Join-Path $ROOT 'installer\SAS_Installer.iss'
if (-not (Test-Path $iss)) { Write-Error 'ISS file not found: ' $iss; exit 5 }
if (-not (Test-Path $ISCC)) { Write-Error 'ISCC.exe not found at: ' $ISCC; exit 6 }

& $ISCC $iss
if ($LASTEXITCODE -ne 0) { Write-Error 'ISCC failed to compile installer'; exit 7 }

Write-Host '7/7 DONE — built updater.exe and SAS_Installer.exe in installer folder'
Write-Host 'Installer:' (Join-Path $ROOT 'installer\SAS_Installer.exe')
Write-Host 'Updater:' (Join-Path $ROOT 'installer\updater.exe')
exit 0

