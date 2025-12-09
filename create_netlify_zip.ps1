# Create Netlify ZIP with only web files
$sourceDir = "C:\Users\DELL\Desktop\sas management system\build\sas_management"
$zipPath = "C:\Users\DELL\Desktop\sas_netlify.zip"
$tempDir = "$env:TEMP\sas_netlify_temp"

Write-Host "=== Creating Netlify ZIP ===" -ForegroundColor Cyan
Write-Host "Source: $sourceDir" -ForegroundColor Gray
Write-Host "Output: $zipPath" -ForegroundColor Gray
Write-Host ""

# Clean temp directory
if (Test-Path $tempDir) {
    Remove-Item $tempDir -Recurse -Force
}
New-Item -ItemType Directory -Path $tempDir -Force | Out-Null

# Find the Python source directory
$pythonSource = "$sourceDir\android\gradle\app\src\main\python\sas_management"

if (!(Test-Path $pythonSource)) {
    Write-Host "[ERROR] Source files not found at: $pythonSource" -ForegroundColor Red
    exit 1
}

Write-Host "Copying web files..." -ForegroundColor Yellow

# Copy templates
if (Test-Path "$pythonSource\templates") {
    Copy-Item "$pythonSource\templates" -Destination "$tempDir\templates" -Recurse -Force
    Write-Host "[OK] Templates copied" -ForegroundColor Green
}

# Copy static files (CSS, JS, images, etc.)
if (Test-Path "$pythonSource\static") {
    Copy-Item "$pythonSource\static" -Destination "$tempDir\static" -Recurse -Force
    Write-Host "[OK] Static files copied" -ForegroundColor Green
}

# Copy any root-level Python files that might be needed
if (Test-Path "$pythonSource\*.py") {
    Copy-Item "$pythonSource\*.py" -Destination $tempDir -Force
    Write-Host "[OK] Python files copied" -ForegroundColor Green
}

# Create ZIP
Write-Host "`nCreating ZIP file..." -ForegroundColor Yellow
if (Test-Path $zipPath) {
    try {
        Remove-Item $zipPath -Force -ErrorAction Stop
    } catch {
        Write-Host "WARNING: Could not remove existing ZIP (file may be open). Creating new version..." -ForegroundColor Yellow
        $timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
        $zipPath = "C:\Users\DELL\Desktop\sas_netlify_$timestamp.zip"
        Write-Host "New ZIP will be created as: $zipPath" -ForegroundColor Gray
    }
}

Compress-Archive -Path "$tempDir\*" -DestinationPath $zipPath -Force

# Cleanup
Remove-Item $tempDir -Recurse -Force

Write-Host ""
Write-Host "[SUCCESS] ZIP created!" -ForegroundColor Green
Write-Host "Location: $zipPath" -ForegroundColor White
$zipInfo = Get-Item $zipPath
Write-Host "Size: $([math]::Round($zipInfo.Length / 1MB, 2)) MB" -ForegroundColor Gray
Write-Host ""

# List contents
Write-Host "ZIP Contents:" -ForegroundColor Cyan
Add-Type -AssemblyName System.IO.Compression.FileSystem
$zip = [System.IO.Compression.ZipFile]::OpenRead($zipPath)
$entries = $zip.Entries | Select-Object -First 20 FullName
foreach ($entry in $entries) {
    Write-Host "  $($entry.FullName)" -ForegroundColor Gray
}
if ($zip.Entries.Count -gt 20) {
    Write-Host "  ... and $($zip.Entries.Count - 20) more files" -ForegroundColor Gray
}
$zip.Dispose()

