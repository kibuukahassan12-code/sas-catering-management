# Rebuild APK with fixed package structure
$projectDir = "C:\Users\DELL\Desktop\sas management system\android_app\android_webview_app"
$JDK17 = "C:\Program Files\Java\jdk-17"

Set-Location $projectDir
$env:JAVA_HOME = $JDK17
$env:PATH = "$JDK17\bin;$env:PATH"

Write-Host "=== Rebuilding Fixed APK ===" -ForegroundColor Cyan
Write-Host "Project: $projectDir" -ForegroundColor Gray
Write-Host "JDK: $JDK17" -ForegroundColor Gray
Write-Host ""

# Verify structure
Write-Host "=== Verifying Package Structure ===" -ForegroundColor Yellow
$mainActivityPath = "$projectDir\app\src\main\java\com\sas\management\MainActivity.java"
if (Test-Path $mainActivityPath) {
    Write-Host "[OK] MainActivity.java found at correct location" -ForegroundColor Green
} else {
    Write-Host "[ERROR] MainActivity.java not found!" -ForegroundColor Red
    exit 1
}

# Clean build
Write-Host "`n=== Cleaning project ===" -ForegroundColor Yellow
.\gradlew.bat clean --no-daemon
if ($LASTEXITCODE -ne 0) {
    Write-Host "WARNING: Clean had issues, but continuing..." -ForegroundColor Yellow
}

# Build APK
Write-Host "`n=== Building APK (5-10 minutes) ===" -ForegroundColor Yellow
Write-Host "Please wait, this may take a while...`n" -ForegroundColor Gray
.\gradlew.bat assembleDebug --no-daemon

# Check result
Write-Host "`n=== Build Result ===" -ForegroundColor Cyan
$apkPath = "$projectDir\app\build\outputs\apk\debug\app-debug.apk"

if (Test-Path $apkPath) {
    Write-Host ""
    Write-Host "========================================" -ForegroundColor Green
    Write-Host "[SUCCESS] APK BUILT!" -ForegroundColor Green
    Write-Host "========================================" -ForegroundColor Green
    Write-Host ""
    Write-Host "APK Location:" -ForegroundColor Cyan
    Write-Host $apkPath -ForegroundColor White
    Write-Host ""
    $apkInfo = Get-Item $apkPath
    Write-Host "File Size: $([math]::Round($apkInfo.Length / 1MB, 2)) MB" -ForegroundColor Gray
    Write-Host "Created: $($apkInfo.CreationTime)" -ForegroundColor Gray
    Write-Host "Modified: $($apkInfo.LastWriteTime)" -ForegroundColor Gray
} else {
    Write-Host ""
    Write-Host "========================================" -ForegroundColor Red
    Write-Host "[FAILED] BUILD FAILED" -ForegroundColor Red
    Write-Host "========================================" -ForegroundColor Red
    Write-Host "APK not found at: $apkPath" -ForegroundColor Yellow
    Write-Host "Check the output above for errors." -ForegroundColor Yellow
    exit 1
}

Write-Host ""

