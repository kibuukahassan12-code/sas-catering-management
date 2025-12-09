$PY = "C:\Users\DELL\AppData\Local\Programs\Python\Python312\python.exe"
$UPDATER = "updater.py"
$OUTFILE = "C:\Users\DELL\Desktop\sas management system\dist\updater.exe"

Write-Host "=== Building updater.exe ==="

# Remove old updater.exe if exists
if (Test-Path "dist\updater.exe") { Remove-Item -Force "dist\updater.exe" -ErrorAction SilentlyContinue }
if (Test-Path "build\updater") { Remove-Item -Recurse -Force "build\updater" -ErrorAction SilentlyContinue }

# Run PyInstaller (use workpath and distpath to avoid conflicts)
& $PY -m PyInstaller --onefile --noconsole --workpath "build\updater_temp" --distpath "dist" $UPDATER
if ($LASTEXITCODE -ne 0) {
    Write-Host "Build failed. See errors above."
    exit 1
}

# Move output
if (!(Test-Path "dist\updater.exe")) {
    Write-Host "ERROR: updater.exe was not generated."
    exit 1
}

Write-Host "Moving updater.exe into dist folder..."
Copy-Item ".\dist\updater.exe" $OUTFILE -Force

Write-Host ""
Write-Host "======================================="
Write-Host "     updater.exe BUILT SUCCESSFULLY"
Write-Host "     Location: $OUTFILE"
Write-Host "======================================="

