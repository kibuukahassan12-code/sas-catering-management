@echo off
title SAS Management Server
cd /d "%~dp0"

echo Starting SAS Management System...
echo.
echo When you see "Running on http://127.0.0.1:5000", open Firefox and go to:
echo   http://127.0.0.1:5000
echo.
python -m sas_management

if errorlevel 1 (
    echo.
    echo Server exited with an error. Check the message above.
    pause
)
