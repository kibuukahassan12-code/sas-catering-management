#!/bin/bash
python3 -m pip install pyinstaller pywebview pystray pillow
python3 -m PyInstaller --noconfirm --clean --windowed app_launcher.py \
  --add-data "templates:templates" \
  --add-data "static:static" \
  --add-data "sas.db:."

