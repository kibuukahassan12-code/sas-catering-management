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
