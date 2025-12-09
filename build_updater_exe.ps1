Write-Host "Building updater.exe from updater.py..."
Write-Host ""

$python = "C:\Users\DELL\AppData\Local\Programs\Python\Python312\python.exe"

# Build updater.exe using PyInstaller
& $python -m PyInstaller --onefile --noconsole --name updater updater.py

if ($LASTEXITCODE -eq 0) {
    Write-Host ""
    Write-Host "✓ updater.exe built successfully!"
    Write-Host "Location: dist\updater.exe"
    Write-Host ""
    Write-Host "Next steps:"
    Write-Host "1. Copy dist\updater.exe to your dist folder"
    Write-Host "2. Rebuild the installer to include updater.exe"
} else {
    Write-Host ""
    Write-Host "✗ Build failed. Check errors above."
}

