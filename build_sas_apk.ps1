# ================================
#  SAS Management - APK Auto Builder
# ================================
Write-Host "`n🟢 Starting SAS Android APK Build..."

# -------- PRECHECKS -----------
Write-Host "`nChecking prerequisites..."

# Java
if (!(java -version 2>$null)) { Write-Host "❌ Java not found"; exit 1 }
Write-Host "✔ Java OK"

# Git
if (!(git --version 2>$null)) { Write-Host "❌ Git not found"; exit 1 }
Write-Host "✔ Git OK"

# Android SDK
if (-not $Env:ANDROID_SDK_ROOT) { Write-Host "❌ ANDROID_SDK_ROOT missing"; exit 1 }
Write-Host "✔ Android SDK OK"

# Briefcase
python -m briefcase --version 2>$null
if ($LASTEXITCODE -ne 0) { Write-Host "❌ Briefcase missing"; exit 1 }
Write-Host "✔ Briefcase OK"

# -------- FIX METADATA -----------
Write-Host "`nFixing pyproject metadata..."

$py = "pyproject.toml"
$content = Get-Content $py

# Ensure proper metadata exists
if ($content -notmatch "license") {
    Add-Content $py "`n[project]"
    Add-Content $py "license = {text = 'Commercial'}"
}

# Create LICENSE file if not exists
if (!(Test-Path "LICENSE")) {
    Set-Content LICENSE "SAS Management System - Commercial License"
}

Write-Host "✔ Metadata fixed"

# -------- CLEAN OLD BUILDS -------
Write-Host "`nCleaning old android build folders..."

Remove-Item -Recurse -Force build\sas_management\android -ErrorAction SilentlyContinue
Remove-Item -Recurse -Force android_build -ErrorAction SilentlyContinue
Write-Host "✔ Old builds removed"

# -------- ADD SAS ICON -----------
Write-Host "`nInstalling SAS App Icon..."

$logo = "sas_logo.png"
if (!(Test-Path $logo)) {
    Write-Host "❌ Missing sas_logo.png"
    exit 1
}

$mipmap = "build\sas_management\android\gradle\app\src\main\res"
$folders = @(
    "mipmap-mdpi","mipmap-hdpi","mipmap-xhdpi",
    "mipmap-xxhdpi","mipmap-xxxhdpi"
)

foreach ($f in $folders) {
    New-Item -ItemType Directory -Force -Path "$mipmap\$f" | Out-Null
    Copy-Item $logo "$mipmap\$f\ic_launcher.png"
}

Write-Host "✔ SAS icon installed"

# -------- CREATE --------
Write-Host "`nCreating Android project..."

python -m briefcase create android
Write-Host "✔ Project created"

# -------- BUILD --------
Write-Host "`nBuilding Android APK (this takes time)..."

python -m briefcase build android
Write-Host "✔ Build completed"

# -------- PACKAGE --------
Write-Host "`nPackaging APK..."

python -m briefcase package android
Write-Host "✔ Packaging completed"

Write-Host "`n🎉 DONE! APK is located in:"
Write-Host "build\sas_management\android\gradle\app\build\outputs\apk\debug\app-debug.apk"
Write-Host "`nYou can copy this file to your phone and install it."

