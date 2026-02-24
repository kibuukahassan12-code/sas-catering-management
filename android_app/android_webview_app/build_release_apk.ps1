# Build SAS Management System Release APK
# This script builds a release (signed) APK for distribution

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "SAS Management System - Release APK Builder" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Check if we're in the right directory
if (-not (Test-Path "app\src\main\java\com\sas\management\MainActivity.java")) {
    Write-Host "Error: Please run this script from the android_webview_app directory" -ForegroundColor Red
    exit 1
}

# Check for keystore
$keystorePath = "sas-release-key.jks"
if (-not (Test-Path $keystorePath)) {
    Write-Host "Creating release keystore..." -ForegroundColor Yellow
    Write-Host "You will be prompted for keystore information." -ForegroundColor Yellow
    Write-Host ""
    
    $keytoolCmd = "keytool -genkey -v -keystore $keystorePath -alias sas-release -keyalg RSA -keysize 2048 -validity 10000"
    
    Write-Host "Running: $keytoolCmd" -ForegroundColor Gray
    Write-Host ""
    Write-Host "Please provide the following information:" -ForegroundColor Yellow
    Write-Host "  - Password (remember this!)" -ForegroundColor White
    Write-Host "  - Name: SAS Best Foods" -ForegroundColor White
    Write-Host "  - Organizational Unit: IT" -ForegroundColor White
    Write-Host "  - Organization: SAS Best Foods" -ForegroundColor White
    Write-Host "  - City: [Your City]" -ForegroundColor White
    Write-Host "  - State: [Your State]" -ForegroundColor White
    Write-Host "  - Country: [Your Country Code, e.g., US]" -ForegroundColor White
    Write-Host ""
    
    Invoke-Expression $keytoolCmd
    
    if ($LASTEXITCODE -ne 0) {
        Write-Host "Error: Failed to create keystore" -ForegroundColor Red
        exit 1
    }
    
    Write-Host ""
    Write-Host "Keystore created successfully!" -ForegroundColor Green
    Write-Host "IMPORTANT: Keep this keystore file safe. You'll need it for future updates." -ForegroundColor Yellow
    Write-Host ""
}

# Create signing config file
$signingConfig = @"
android {
    signingConfigs {
        release {
            storeFile file('$keystorePath')
            storePassword 'YOUR_STORE_PASSWORD'
            keyAlias 'sas-release'
            keyPassword 'YOUR_KEY_PASSWORD'
        }
    }
    buildTypes {
        release {
            signingConfig signingConfigs.release
        }
    }
}
"@

Write-Host "Note: For production builds, you need to configure signing in app/build.gradle" -ForegroundColor Yellow
Write-Host ""

# Generate icons
Write-Host "[1/4] Generating app icons..." -ForegroundColor Yellow
if (Test-Path "generate_icons.py") {
    python generate_icons.py
}

# Clean
Write-Host ""
Write-Host "[2/4] Cleaning previous builds..." -ForegroundColor Yellow
$gradleCmd = ".\gradlew.bat"
if (Test-Path "gradlew_jdk17.bat") {
    $gradleCmd = ".\gradlew_jdk17.bat"
}

& $gradleCmd clean

# Build release
Write-Host ""
Write-Host "[3/4] Building release APK..." -ForegroundColor Yellow
Write-Host "This may take a few minutes..." -ForegroundColor Gray

& $gradleCmd assembleRelease

if ($LASTEXITCODE -ne 0) {
    Write-Host ""
    Write-Host "Error: Build failed. Please check the error messages above." -ForegroundColor Red
    exit 1
}

# Locate APK
Write-Host ""
Write-Host "[4/4] Locating release APK..." -ForegroundColor Yellow

$apkPath = "app\build\outputs\apk\release\app-release.apk"
if (Test-Path $apkPath) {
    $apkInfo = Get-Item $apkPath
    $apkSize = [math]::Round($apkInfo.Length / 1MB, 2)
    
    Write-Host ""
    Write-Host "========================================" -ForegroundColor Green
    Write-Host "Release Build Successful!" -ForegroundColor Green
    Write-Host "========================================" -ForegroundColor Green
    Write-Host ""
    Write-Host "APK Location: $($apkInfo.FullName)" -ForegroundColor Cyan
    Write-Host "APK Size: $apkSize MB" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "This APK is ready for distribution!" -ForegroundColor Green
} else {
    Write-Host ""
    Write-Host "Error: Release APK not found at expected location: $apkPath" -ForegroundColor Red
    exit 1
}

