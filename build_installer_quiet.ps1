Write-Host "Building installer... Please wait (this may take several minutes)..."
Write-Host ""

$issPath = "C:\Users\DELL\Desktop\sas management system\installer\SAS_Installer.iss"
$isccPath = "C:\Program Files (x86)\Inno Setup 6\ISCC.exe"

# Run ISCC with quiet progress mode
& $isccPath /Qp $issPath

if ($LASTEXITCODE -eq 0) {
    Write-Host ""
    Write-Host "SUCCESS! Installer created at:"
    Write-Host "installer\SAS_Installer.exe"
} else {
    Write-Host ""
    Write-Host "Build failed. Check errors above."
}

