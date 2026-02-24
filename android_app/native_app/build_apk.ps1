# Build APK Script for SAS Management Android App
# Run this script to generate the APK file

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "SAS Management - APK Build Script" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Check if we're in the right directory
if (-not (Test-Path "app\build.gradle")) {
    Write-Host "Error: Please run this script from the android_app/native_app directory" -ForegroundColor Red
    exit 1
}

# Check if Gradle wrapper exists
if (-not (Test-Path "gradlew.bat")) {
    Write-Host "Error: Gradle wrapper not found. Please initialize the project in Android Studio first." -ForegroundColor Red
    exit 1
}

Write-Host "Step 1: Cleaning previous builds..." -ForegroundColor Yellow
& .\gradlew.bat clean
if ($LASTEXITCODE -ne 0) {
    Write-Host "Error: Clean failed" -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "Step 2: Building debug APK..." -ForegroundColor Yellow
& .\gradlew.bat assembleDebug
if ($LASTEXITCODE -ne 0) {
    Write-Host "Error: Build failed" -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "Step 3: Checking APK location..." -ForegroundColor Yellow
$apkPath = "app\build\outputs\apk\debug\app-debug.apk"
if (Test-Path $apkPath) {
    $apkSize = (Get-Item $apkPath).Length / 1MB
    Write-Host ""
    Write-Host "========================================" -ForegroundColor Green
    Write-Host "✓ APK Build Successful!" -ForegroundColor Green
    Write-Host "========================================" -ForegroundColor Green
    Write-Host "APK Location: $apkPath" -ForegroundColor Cyan
    Write-Host "APK Size: $([math]::Round($apkSize, 2)) MB" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "To install on device:" -ForegroundColor Yellow
    Write-Host "  adb install $apkPath" -ForegroundColor White
    Write-Host ""
    
    # Ask if user wants to copy to root
    $copy = Read-Host "Copy APK to project root? (y/n)"
    if ($copy -eq "y" -or $copy -eq "Y") {
        $rootPath = "..\..\sas-management-app.apk"
        Copy-Item $apkPath $rootPath -Force
        Write-Host "APK copied to: $rootPath" -ForegroundColor Green
    }
} else {
    Write-Host "Error: APK not found at expected location" -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "Build complete!" -ForegroundColor Green

