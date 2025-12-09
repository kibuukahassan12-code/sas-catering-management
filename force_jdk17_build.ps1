# === FORCE ANDROID BUILD TO USE JDK 17 ONLY ===

Write-Host "=== FIXING ANDROID BUILD ENVIRONMENT ===" -ForegroundColor Cyan

$Project = "C:\Users\DELL\Desktop\sas management system\android_app\android_webview_app"
$JDK17   = "C:\Program Files\Java\jdk-17"

if (!(Test-Path $JDK17)) {
    Write-Error "JDK 17 NOT INSTALLED. Install from: https://adoptium.net/temurin/releases/?version=17"
    exit 1
}

# Go to project folder
Set-Location $Project

# 1. Force JAVA_HOME
$Env:JAVA_HOME = $JDK17
try {
    [System.Environment]::SetEnvironmentVariable("JAVA_HOME", $JDK17, "Machine")
    Write-Host "[OK] JAVA_HOME set to JDK 17 (system-wide)" -ForegroundColor Green
} catch {
    Write-Host "[OK] JAVA_HOME set to JDK 17 (current session)" -ForegroundColor Yellow
    Write-Host "Note: System-wide setting requires admin privileges" -ForegroundColor Gray
}

# 2. Patch gradle.properties
@"
org.gradle.java.home=$JDK17
android.useAndroidX=true
android.enableJetifier=true
org.gradle.jvmargs=-Xmx2048m -Dfile.encoding=UTF-8
"@ | Out-File "gradle.properties" -Encoding ASCII
Write-Host "[OK] gradle.properties updated" -ForegroundColor Green

# 3. Patch local.properties
$sdkDir = "$env:LOCALAPPDATA\Android\Sdk"
if (!(Test-Path $sdkDir)) {
    $sdkDir = "C:\Users\DELL\AppData\Local\Android\Sdk"
}

@"
sdk.dir=$($sdkDir.Replace('\', '\\'))
jdk.dir=$JDK17
"@ | Out-File "local.properties" -Encoding ASCII
Write-Host "[OK] local.properties updated" -ForegroundColor Green

# 4. Patch gradlew.bat — force correct Java
$gradlewContent = Get-Content "gradlew.bat" -Raw
$gradlewContent = $gradlewContent -replace 'SET "JAVA_EXE=.*"', "SET `"JAVA_EXE=$JDK17\bin\java.exe`""
$gradlewContent = $gradlewContent -replace 'SET JAVA_EXE=.*', "SET `"JAVA_EXE=$JDK17\bin\java.exe`""
Set-Content "gradlew.bat" -Value $gradlewContent -NoNewline
Write-Host "[OK] gradlew.bat patched to use JDK 17" -ForegroundColor Green

# 5. Clean project
Write-Host "`n=== CLEANING PROJECT ===" -ForegroundColor Yellow
$env:JAVA_HOME = $JDK17
$env:PATH = "$JDK17\bin;$env:PATH"
cmd /c "gradlew.bat clean --no-daemon"
if ($LASTEXITCODE -ne 0) {
    Write-Host "WARNING: Clean had issues, but continuing..." -ForegroundColor Yellow
}

# 6. Build APK
Write-Host "`n=== BUILDING APK (5-10 minutes) ===" -ForegroundColor Yellow
Write-Host "Please wait, this may take a while...`n" -ForegroundColor Gray
$env:JAVA_HOME = $JDK17
$env:PATH = "$JDK17\bin;$env:PATH"
cmd /c "gradlew.bat assembleDebug --no-daemon"

# 7. Check result
Write-Host "`n=== Build Result ===" -ForegroundColor Cyan
$apkPath = "$Project\app\build\outputs\apk\debug\app-debug.apk"

if (Test-Path $apkPath) {
    Write-Host ""
    Write-Host "========================================" -ForegroundColor Green
    Write-Host "[SUCCESS] APK BUILT!" -ForegroundColor Green
    Write-Host "========================================" -ForegroundColor Green
    Write-Host "APK Location:" -ForegroundColor Cyan
    Write-Host $apkPath -ForegroundColor White
    $apkInfo = Get-Item $apkPath
    Write-Host "File Size: $([math]::Round($apkInfo.Length / 1MB, 2)) MB" -ForegroundColor Gray
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
Write-Host "=== DONE ===" -ForegroundColor Green

