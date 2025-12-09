# ========================================
# FINAL APK FIX — DETECT, REPAIR, AND BUILD (ONE COMMAND)
# ========================================

$ErrorActionPreference = "Stop"

Write-Host "`n🔥 FINAL APK FIX — DETECT, REPAIR, AND BUILD`n" -ForegroundColor Cyan

# 1. Detect correct project path
$basePath = "C:\Users\DELL\Desktop\sas management system"
$project = Join-Path $basePath "android_app\android_webview_app"

if (-not (Test-Path $project)) {
    $project = Join-Path $basePath "android_webview_app"
}

if (-not (Test-Path $project)) {
    $project = $basePath
}

Write-Host "📌 Using project folder: $project" -ForegroundColor Green
Set-Location $project

# 2. Create wrapper directory
Write-Host "`n[1/7] Creating wrapper directory..." -ForegroundColor Yellow
$wrapperDir = Join-Path $project "gradle\wrapper"
New-Item -ItemType Directory -Force -Path $wrapperDir | Out-Null
Write-Host "  ✓ Wrapper directory created" -ForegroundColor Green

# 3. Write wrapper properties
Write-Host "`n[2/7] Writing wrapper properties..." -ForegroundColor Yellow
$wrapperProps = @"
distributionBase=GRADLE_USER_HOME
distributionPath=wrapper/dists
distributionUrl=https\://services.gradle.org/distributions/gradle-8.5-bin.zip
zipStoreBase=GRADLE_USER_HOME
zipStorePath=wrapper/dists
"@
$wrapperProps | Set-Content (Join-Path $wrapperDir "gradle-wrapper.properties") -Encoding UTF8
Write-Host "  ✓ Wrapper properties written" -ForegroundColor Green

# 4. Download official Gradle wrapper jar
Write-Host "`n[3/7] Downloading Gradle wrapper JAR..." -ForegroundColor Yellow
$jarPath = Join-Path $wrapperDir "gradle-wrapper.jar"
$jarUrl = "https://raw.githubusercontent.com/gradle/gradle/v8.5.0/gradle/wrapper/gradle-wrapper.jar"

try {
    Invoke-WebRequest -Uri $jarUrl -OutFile $jarPath -UseBasicParsing -ErrorAction Stop
    Write-Host "  ✓ gradle-wrapper.jar downloaded" -ForegroundColor Green
} catch {
    Write-Host "  ⚠ Primary URL failed, trying alternative..." -ForegroundColor Yellow
    try {
        # Try alternative URL
        $altUrl = "https://github.com/gradle/gradle/raw/v8.5.0/gradle/wrapper/gradle-wrapper.jar"
        Invoke-WebRequest -Uri $altUrl -OutFile $jarPath -UseBasicParsing -ErrorAction Stop
        Write-Host "  ✓ gradle-wrapper.jar downloaded (alternative)" -ForegroundColor Green
    } catch {
        Write-Host "  ⚠ Download failed, using Gradle to generate..." -ForegroundColor Yellow
        $gradle = Get-Command gradle -ErrorAction SilentlyContinue
        if ($gradle) {
            & gradle wrapper --gradle-version 8.5 2>&1 | Out-Null
            Write-Host "  ✓ Generated using local Gradle" -ForegroundColor Green
        } else {
            Write-Host "  ❌ Could not download or generate wrapper JAR" -ForegroundColor Red
            Write-Host "  Please ensure you have internet connection or Gradle installed" -ForegroundColor Yellow
        }
    }
}

# 5. Create gradlew.bat
Write-Host "`n[4/7] Creating gradlew.bat..." -ForegroundColor Yellow
$gradlewBat = @"
@ECHO OFF
SET DIR=%~dp0
SET CLASSPATH=%DIR%gradle\wrapper\gradle-wrapper.jar

REM Find Java
if defined JAVA_HOME (
    SET JAVA_EXE=%JAVA_HOME%\bin\java.exe
) else (
    SET JAVA_EXE=java.exe
)

%JAVA_EXE% -classpath "%CLASSPATH%" org.gradle.wrapper.GradleWrapperMain %*
IF %ERRORLEVEL% NEQ 0 EXIT /B %ERRORLEVEL%
"@
$gradlewBat | Set-Content (Join-Path $project "gradlew.bat") -Encoding ASCII
Write-Host "  ✓ gradlew.bat created" -ForegroundColor Green

# 6. Create gradlew (Linux/Mac)
Write-Host "`n[5/7] Creating gradlew (Linux/Mac)..." -ForegroundColor Yellow
$gradlew = @"
#!/bin/sh
DIR="$( cd "$( dirname "`$0" )" && pwd )"
CLASSPATH="`$DIR/gradle/wrapper/gradle-wrapper.jar"
java -classpath "`$CLASSPATH" org.gradle.wrapper.GradleWrapperMain "`$@"
"@
$gradlew | Set-Content (Join-Path $project "gradlew") -Encoding UTF8
Write-Host "  ✓ gradlew created" -ForegroundColor Green

# 7. Verify and fix project structure
Write-Host "`n[6/7] Verifying project structure..." -ForegroundColor Yellow

# Ensure MainActivity is in correct package
$mainActivityPath = Join-Path $project "app\src\main\java\com\sas\management\MainActivity.java"
if (-not (Test-Path $mainActivityPath)) {
    # Check if it's in wrong location
    $wrongPath = Join-Path $project "app\src\main\java\com\sas\webview\MainActivity.java"
    if (Test-Path $wrongPath) {
        Write-Host "  Fixing MainActivity package location..." -ForegroundColor Yellow
        $managementDir = Join-Path $project "app\src\main\java\com\sas\management"
        New-Item -ItemType Directory -Force -Path $managementDir | Out-Null
        $content = Get-Content $wrongPath -Raw
        $content = $content -replace "package com\.sas\.webview;", "package com.sas.management;"
        $content | Set-Content $mainActivityPath -NoNewline
        Remove-Item (Split-Path $wrongPath) -Recurse -Force -ErrorAction SilentlyContinue
        Write-Host "  ✓ MainActivity moved to correct package" -ForegroundColor Green
    }
}

# Ensure icons exist
$logoSrc = Join-Path $basePath "sas_logo.png"
if (-not (Test-Path $logoSrc)) {
    $logoSrc = Join-Path $basePath "dist\sas_logo.png"
}

if (Test-Path $logoSrc) {
    $mipmaps = @('mipmap-mdpi', 'mipmap-hdpi', 'mipmap-xhdpi', 'mipmap-xxhdpi', 'mipmap-xxxhdpi')
    foreach ($m in $mipmaps) {
        $mipmapPath = Join-Path $project "app\src\main\res\$m"
        if (-not (Test-Path $mipmapPath)) {
            New-Item -ItemType Directory -Force -Path $mipmapPath | Out-Null
        }
        $iconPath = Join-Path $mipmapPath "ic_launcher.png"
        if (-not (Test-Path $iconPath)) {
            Copy-Item $logoSrc $iconPath -Force
        }
    }
    Write-Host "  ✓ Icons verified" -ForegroundColor Green
}

# Verify required files
$requiredFiles = @(
    "app\src\main\AndroidManifest.xml",
    "app\src\main\java\com\sas\management\MainActivity.java",
    "app\build.gradle",
    "build.gradle",
    "settings.gradle"
)

$allPresent = $true
foreach ($file in $requiredFiles) {
    $fullPath = Join-Path $project $file
    if (-not (Test-Path $fullPath)) {
        Write-Host "  ❌ $file MISSING" -ForegroundColor Red
        $allPresent = $false
    }
}

if ($allPresent) {
    Write-Host "  ✓ All required files present" -ForegroundColor Green
} else {
    Write-Host "  ⚠ Some files missing, but continuing..." -ForegroundColor Yellow
}

# 8. Build APK
Write-Host "`n[7/7] Building APK..." -ForegroundColor Cyan
Write-Host "🚀 This may take several minutes...`n" -ForegroundColor Yellow

$gradlewPath = Join-Path $project "gradlew.bat"
if (Test-Path $gradlewPath) {
    Set-Location $project
    
    # Clean first
    Write-Host "Cleaning previous build..." -ForegroundColor Gray
    & $gradlewPath clean 2>&1 | Out-Null
    
    # Build
    Write-Host "Assembling debug APK..." -ForegroundColor Gray
    & $gradlewPath assembleDebug --no-daemon --stacktrace
    
    if ($LASTEXITCODE -eq 0) {
        $apkPath = Join-Path $project "app\build\outputs\apk\debug\app-debug.apk"
        if (Test-Path $apkPath) {
            $fullPath = (Resolve-Path $apkPath).Path
            $size = (Get-Item $apkPath).Length / 1MB
            
            Write-Host "`n============================================" -ForegroundColor Green
            Write-Host "  ✅ BUILD COMPLETE!" -ForegroundColor Green
            Write-Host "============================================" -ForegroundColor Green
            Write-Host "📦 APK Location: $fullPath" -ForegroundColor Cyan
            Write-Host "📊 APK Size: $([math]::Round($size, 2)) MB" -ForegroundColor Cyan
            Write-Host "============================================" -ForegroundColor Green
            
            # Open folder
            Start-Process explorer.exe -ArgumentList "/select,`"$fullPath`""
        } else {
            Write-Host "`n⚠ Build succeeded but APK not found at expected location" -ForegroundColor Yellow
            Write-Host "Expected: $apkPath" -ForegroundColor Gray
        }
    } else {
        Write-Host "`n❌ BUILD FAILED" -ForegroundColor Red
        Write-Host "Exit code: $LASTEXITCODE" -ForegroundColor Yellow
        Write-Host "Check the output above for errors." -ForegroundColor Yellow
        exit $LASTEXITCODE
    }
} else {
    Write-Host "`n❌ ERROR: gradlew.bat not found!" -ForegroundColor Red
    Write-Host "Path checked: $gradlewPath" -ForegroundColor Yellow
    exit 1
}

