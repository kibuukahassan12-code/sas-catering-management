# Build SAS Management System APK
# This script builds the Android APK with all SAS features and branding

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "SAS Management System - APK Builder" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Check if we're in the right directory
if (-not (Test-Path "app\src\main\java\com\sas\management\MainActivity.java")) {
    Write-Host "Error: Please run this script from the android_webview_app directory" -ForegroundColor Red
    exit 1
}

# Step 1: Generate icons from SAS logo
Write-Host "[1/5] Generating app icons from SAS logo..." -ForegroundColor Yellow
if (Test-Path "generate_icons.py") {
    python generate_icons.py
    if ($LASTEXITCODE -ne 0) {
        Write-Host "Warning: Icon generation had issues, but continuing..." -ForegroundColor Yellow
    }
} else {
    Write-Host "Warning: generate_icons.py not found, skipping icon generation" -ForegroundColor Yellow
}

# Step 2: Clean previous builds
Write-Host ""
Write-Host "[2/5] Cleaning previous builds..." -ForegroundColor Yellow
if (Test-Path "app\build") {
    Remove-Item -Recurse -Force "app\build" -ErrorAction SilentlyContinue
}
if (Test-Path "build") {
    Remove-Item -Recurse -Force "build" -ErrorAction SilentlyContinue
}

# Step 3: Check for Gradle wrapper
Write-Host ""
Write-Host "[3/5] Checking Gradle setup..." -ForegroundColor Yellow
if (-not (Test-Path "gradlew.bat")) {
    Write-Host "Error: gradlew.bat not found. Please ensure Gradle wrapper is set up." -ForegroundColor Red
    exit 1
}

# Step 4: Build debug APK
Write-Host ""
Write-Host "[4/5] Building debug APK..." -ForegroundColor Yellow
Write-Host "This may take a few minutes..." -ForegroundColor Gray

$gradleCmd = ".\gradlew.bat"
if (Test-Path "gradlew_jdk17.bat") {
    $gradleCmd = ".\gradlew_jdk17.bat"
}

& $gradleCmd clean assembleDebug

if ($LASTEXITCODE -ne 0) {
    Write-Host ""
    Write-Host "Error: Build failed. Please check the error messages above." -ForegroundColor Red
    exit 1
}

# Step 5: Locate and report APK
Write-Host ""
Write-Host "[5/5] Locating generated APK..." -ForegroundColor Yellow

$apkPath = "app\build\outputs\apk\debug\app-debug.apk"
if (Test-Path $apkPath) {
    $apkInfo = Get-Item $apkPath
    $apkSize = [math]::Round($apkInfo.Length / 1MB, 2)
    
    Write-Host ""
    Write-Host "========================================" -ForegroundColor Green
    Write-Host "Build Successful!" -ForegroundColor Green
    Write-Host "========================================" -ForegroundColor Green
    Write-Host ""
    Write-Host "APK Location: $($apkInfo.FullName)" -ForegroundColor Cyan
    Write-Host "APK Size: $apkSize MB" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "The APK includes:" -ForegroundColor Yellow
    Write-Host "  - SAS logo as app icon" -ForegroundColor White
    Write-Host "  - Full SAS Management System UI" -ForegroundColor White
    Write-Host "  - All modules and features" -ForegroundColor White
    Write-Host "  - WebView-based interface" -ForegroundColor White
    Write-Host ""
    Write-Host "To install on your device:" -ForegroundColor Yellow
    Write-Host "  1. Enable 'Install from Unknown Sources' in Android settings" -ForegroundColor White
    Write-Host "  2. Transfer the APK to your device" -ForegroundColor White
    Write-Host "  3. Open the APK file and install" -ForegroundColor White
    Write-Host ""
    Write-Host "Note: The app connects to http://127.0.0.1:5000 by default." -ForegroundColor Yellow
    Write-Host "      Update strings.xml to change the server URL for production." -ForegroundColor Yellow
    Write-Host ""
    
    # Optionally open the folder
    $openFolder = Read-Host "Open folder containing APK? (Y/N)"
    if ($openFolder -eq "Y" -or $openFolder -eq "y") {
        Start-Process explorer.exe -ArgumentList "/select,`"$($apkInfo.FullName)`""
    }
} else {
    Write-Host ""
    Write-Host "Error: APK not found at expected location: $apkPath" -ForegroundColor Red
    Write-Host "Please check the build output for errors." -ForegroundColor Red
    exit 1
}

