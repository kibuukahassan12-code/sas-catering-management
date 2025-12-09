Write-Host "=== SAS Management System | Windows GUI Build ==="



$python = (Get-Command python -ErrorAction SilentlyContinue).Source

if (-not $python) { $python = (Get-Command py -ErrorAction SilentlyContinue).Source }

if (-not $python) { Write-Error "Python not found!"; exit 1 }



Write-Host "Installing dependencies..."

& $python -m pip install --upgrade pip setuptools wheel --user

& $python -m pip install pyinstaller pywebview pystray pillow waitress --user

& $python -m pip install flask_login flask_sqlalchemy flask_limiter flask_bcrypt flask_wtf python-dotenv wtforms --user



Write-Host "Building EXE..."



$extras = '--add-data "templates;templates" --add-data "static;static" --add-data "sas.db;."'

$hidden = '--hidden-import flask_login --hidden-import flask_sqlalchemy --hidden-import flask_limiter --hidden-import flask_bcrypt --hidden-import flask_wtf --hidden-import wtforms --hidden-import dotenv --hidden-import pystray --hidden-import webview'



$cmd = "$python -m PyInstaller --noconfirm --clean --onefile --windowed $extras $hidden app_launcher.py"

Invoke-Expression $cmd



Write-Host "GUI Build Complete → dist/app_launcher.exe"

