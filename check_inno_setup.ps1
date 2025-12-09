Write-Host "Checking for Inno Setup installation..."
Write-Host ""

$paths = @(
    "C:\Program Files (x86)\Inno Setup 6\ISCC.exe",
    "C:\Program Files\Inno Setup 6\ISCC.exe",
    "C:\Program Files\Inno Setup\ISCC.exe",
    "$env:LOCALAPPDATA\Programs\Inno Setup\ISCC.exe"
)

$found = $false
foreach ($path in $paths) {
    if (Test-Path $path) {
        Write-Host "✓ Found ISCC.exe at: $path"
        $found = $true
        break
    }
}

if (-not $found) {
    Write-Host "✗ Inno Setup ISCC.exe not found in standard locations"
    Write-Host ""
    Write-Host "Please install Inno Setup from:"
    Write-Host "https://jrsoftware.org/isdl.php"
    Write-Host ""
    Write-Host "Or if you have it installed elsewhere, update the path in build_installer_complete.ps1"
} else {
    Write-Host ""
    Write-Host "Inno Setup is ready to use!"
}

