# Simple Android APK Build Script
$projectDir = "C:\Users\DELL\Desktop\sas management system\android_app\android_webview_app"
Set-Location $projectDir

$JDK17 = "C:\Program Files\Java\jdk-17"
$Env:JAVA_HOME = $JDK17
$Env:PATH = "$JDK17\bin;$Env:PATH"

Write-Host "=== FIXING ANDROID BUILD ===" -ForegroundColor Cyan

# 1. Force JDK 17
if (!(Test-Path $JDK17)) {
    Write-Host "ERROR: JDK 17 NOT FOUND. Install Temurin JDK 17 first:" -ForegroundColor Red
    Write-Host "https://adoptium.net/temurin/releases/?version=17" -ForegroundColor Yellow
    exit 1
}

Write-Host "[OK] Using JDK 17: $JDK17" -ForegroundColor Green

# 2. Tell Gradle EXACTLY which Java to use
"org.gradle.java.home=$JDK17" | Out-File gradle.properties -Encoding ASCII
Write-Host "[OK] gradle.properties updated" -ForegroundColor Green

# 3. local.properties
"jdk.dir=$JDK17" | Out-File local.properties -Encoding ASCII
Write-Host "[OK] local.properties updated" -ForegroundColor Green

# 4. Patch gradlew.bat
$gradlew = "gradlew.bat"
if (Test-Path $gradlew) {
    $content = Get-Content $gradlew -Raw
    $content = $content -replace 'SET "JAVA_EXE=.*"', "SET `"JAVA_EXE=$JDK17\bin\java.exe`""
    $content = $content -replace 'SET JAVA_EXE=.*', "SET `"JAVA_EXE=$JDK17\bin\java.exe`""
    Set-Content $gradlew -Value $content -NoNewline
    Write-Host "[OK] gradlew.bat patched" -ForegroundColor Green
}

# 5. Clean project
Write-Host "`n=== Cleaning project ===" -ForegroundColor Yellow
.\gradlew.bat clean --no-daemon
if ($LASTEXITCODE -ne 0) {
    Write-Host "WARNING: Clean had issues, but continuing..." -ForegroundColor Yellow
}

# 6. Build APK
Write-Host "`n=== Building APK (5-10 minutes) ===" -ForegroundColor Yellow
Write-Host "Please wait, this may take a while...`n" -ForegroundColor Gray
.\gradlew.bat assembleDebug --no-daemon

# Check result
Write-Host "`n=== Build Result ===" -ForegroundColor Cyan
$apkPath = "app\build\outputs\apk\debug\app-debug.apk"

if (Test-Path $apkPath) {
    Write-Host ""
    Write-Host "========================================" -ForegroundColor Green
    Write-Host "[SUCCESS] APK BUILT!" -ForegroundColor Green
    Write-Host "========================================" -ForegroundColor Green
    $fullPath = Resolve-Path $apkPath
    Write-Host "APK Location:" -ForegroundColor Cyan
    Write-Host $fullPath -ForegroundColor White
    $apkInfo = Get-Item $apkPath
    Write-Host "File Size: $([math]::Round($apkInfo.Length / 1MB, 2)) MB" -ForegroundColor Gray
} else {
    Write-Host ""
    Write-Host "========================================" -ForegroundColor Red
    Write-Host "[FAILED] BUILD FAILED" -ForegroundColor Red
    Write-Host "========================================" -ForegroundColor Red
    Write-Host "APK not found. Check errors above." -ForegroundColor Yellow
    exit 1
}

Write-Host ""
Write-Host "=== DONE ===" -ForegroundColor Green
Write-Host "APK should now be located at:" -ForegroundColor Cyan
Write-Host "app\build\outputs\apk\debug\app-debug.apk" -ForegroundColor White

