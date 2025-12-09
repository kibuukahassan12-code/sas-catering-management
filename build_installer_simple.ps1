$base='C:\Users\DELL\Desktop\sas management system'
$dist="$base\dist\"
$icoSrc="$base\sas_logo.ico"
$icoDst="$dist\sas_logo.ico"

# Copy icon into DIST
Write-Host "Copying icon to dist folder..."
Copy-Item -Path $icoSrc -Destination $icoDst -Force

# Compile with Inno Setup (ISCC)
Write-Host "Building installer..."
& 'C:\Program Files (x86)\Inno Setup 6\ISCC.exe' "$base\installer\SAS_Installer.iss"

if ($LASTEXITCODE -eq 0) {
    Write-Host ''
    Write-Host '===================================================='
    Write-Host 'BUILD COMPLETE  ✔   Installer is ready!'
    Write-Host "Installer Path: $base\installer\SAS_Installer.exe"
    Write-Host '===================================================='
} else {
    Write-Host ''
    Write-Host 'BUILD FAILED - Check errors above'
    exit 1
}

