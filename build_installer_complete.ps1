$base='C:\Users\DELL\Desktop\sas management system'
$dist="$base\dist\"
$icoSrc="$base\sas_logo.ico"
$icoDst="$dist\sas_logo.ico"

Write-Host "=========================================="
Write-Host "  Building SAS Management System Installer"
Write-Host "=========================================="
Write-Host ""

# Copy icon into DIST if it doesn't exist
if (-not (Test-Path $icoDst)) {
    Write-Host "Copying icon to dist folder..."
    Copy-Item -Path $icoSrc -Destination $icoDst -Force
    Write-Host "Icon copied"
} else {
    Write-Host "Icon already exists in dist folder"
}

Write-Host ""
Write-Host "Compiling installer (this may take a few minutes)..."
Write-Host "Please wait - compressing files..."
Write-Host ""

# Compile with Inno Setup (ISCC)
& 'C:\Program Files (x86)\Inno Setup 6\ISCC.exe' "$base\installer\SAS_Installer.iss"

if ($LASTEXITCODE -eq 0) {
    Write-Host ""
    Write-Host "===================================================="
    Write-Host "  BUILD COMPLETE - Installer is ready!"
    Write-Host "===================================================="
    Write-Host "Installer Path: $base\installer\SAS_Installer.exe"
    Write-Host ""
    Write-Host "The installer will create:"
    Write-Host "  - Desktop shortcut"
    Write-Host "  - Start Menu shortcut"
    Write-Host "===================================================="
} else {
    Write-Host ""
    Write-Host "BUILD FAILED - Check errors above"
    exit 1
}
