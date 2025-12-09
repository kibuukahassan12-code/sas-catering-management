# ========================================
# FINAL APK FIX — DETECT, REPAIR, AND BUILD
# ========================================

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
    Write-Host "  ⚠ Could not download from primary URL, trying alternative..." -ForegroundColor Yellow
    try {
        $altUrl = "https://github.com/gradle/gradle/raw/v8.5.0/gradle/wrapper/gradle-wrapper.jar"
        Invoke-WebRequest -Uri $altUrl -OutFile $jarPath -UseBasicParsing -ErrorAction Stop
        Write-Host "  ✓ gradle-wrapper.jar downloaded (alternative)" -ForegroundColor Green
    } catch {
        Write-Host "  ⚠ Download failed. Will use Gradle to generate it." -ForegroundColor Yellow
        $gradle = Get-Command gradle -ErrorAction SilentlyContinue
        if ($gradle) {
            & gradle wrapper --gradle-version 8.5 2>&1 | Out-Null
            Write-Host "  ✓ Generated using local Gradle" -ForegroundColor Green
        } else {
            Write-Host "  ❌ Could not download or generate wrapper JAR" -ForegroundColor Red
        }
    }
}

# 5. Create gradlew.bat
Write-Host "`n[4/7] Creating gradlew.bat..." -ForegroundColor Yellow
$gradlewBat = @"
@ECHO OFF
SET DIR=%~dp0
SET CLASSPATH=%DIR%gradle\wrapper\gradle-wrapper.jar

"%JAVA_HOME%\bin\java.exe" -classpath "%CLASSPATH%" org.gradle.wrapper.GradleWrapperMain %*
IF %ERRORLEVEL% NEQ 0 EXIT /B %ERRORLEVEL%
"@

# Try to find Java if JAVA_HOME not set
$javaExe = "java.exe"
if ($env:JAVA_HOME) {
    $javaExe = Join-Path $env:JAVA_HOME "bin\java.exe"
} else {
    $javaCmd = Get-Command java -ErrorAction SilentlyContinue
    if ($javaCmd) {
        $javaExe = "java"
    }
}

$gradlewBat = $gradlewBat -replace '"%JAVA_HOME%\\bin\\java.exe"', "`"$javaExe`""
$gradlewBat | Set-Content (Join-Path $project "gradlew.bat") -Encoding ASCII
Write-Host "  ✓ gradlew.bat created" -ForegroundColor Green

# 6. Create gradlew (Linux/Mac)
Write-Host "`n[5/7] Creating gradlew (Linux/Mac)..." -ForegroundColor Yellow
$gradlew = @"
#!/bin/sh
DIR="$( cd "$( dirname "$0" )" && pwd )"
CLASSPATH="$DIR/gradle/wrapper/gradle-wrapper.jar"
java -classpath "$CLASSPATH" org.gradle.wrapper.GradleWrapperMain "$@"
"@
$gradlew | Set-Content (Join-Path $project "gradlew") -Encoding UTF8
Write-Host "  ✓ gradlew created" -ForegroundColor Green

# 7. Verify project structure
Write-Host "`n[6/7] Verifying project structure..." -ForegroundColor Yellow
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
    if (Test-Path $fullPath) {
        Write-Host "  ✓ $file" -ForegroundColor Green
    } else {
        Write-Host "  ❌ $file MISSING" -ForegroundColor Red
        $allPresent = $false
    }
}

if (-not $allPresent) {
    Write-Host "`n⚠ Some required files are missing. Build may fail." -ForegroundColor Yellow
}

# 8. Build APK
Write-Host "`n[7/7] Building APK..." -ForegroundColor Cyan
Write-Host "🚀 This may take several minutes...`n" -ForegroundColor Yellow

$gradlewPath = Join-Path $project "gradlew.bat"
if (Test-Path $gradlewPath) {
    Set-Location $project
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
        }
    } else {
        Write-Host "`n❌ BUILD FAILED" -ForegroundColor Red
        Write-Host "Check the output above for errors." -ForegroundColor Yellow
        exit $LASTEXITCODE
    }
} else {
    Write-Host "`n❌ ERROR: gradlew.bat not found!" -ForegroundColor Red
    exit 1
}

