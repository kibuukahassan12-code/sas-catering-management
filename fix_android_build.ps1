Write-Host "=== FIXING ANDROID BUILD ===" -ForegroundColor Cyan

# 1. Force JDK 17
$JDK17 = "C:\Program Files\Java\jdk-17"

if (!(Test-Path $JDK17)) {
    Write-Host "ERROR: JDK 17 NOT FOUND. Install Temurin JDK 17 first:" -ForegroundColor Red
    Write-Host "https://adoptium.net/temurin/releases/?version=17" -ForegroundColor Yellow
    exit 1
}

Write-Host "[OK] Using JDK 17: $JDK17" -ForegroundColor Green
$Env:JAVA_HOME = $JDK17
try {
    [System.Environment]::SetEnvironmentVariable("JAVA_HOME", $JDK17, "Machine")
    Write-Host "[OK] JAVA_HOME set (system-wide)" -ForegroundColor Green
} catch {
    Write-Host "[OK] JAVA_HOME set (current session)" -ForegroundColor Yellow
    Write-Host "Note: System-wide setting requires admin privileges" -ForegroundColor Gray
}

# 2. Tell Gradle EXACTLY which Java to use
$projectDir = "C:\Users\DELL\Desktop\sas management system\android_app\android_webview_app"
Set-Location $projectDir

"org.gradle.java.home=$JDK17" | Out-File gradle.properties -Encoding ASCII
Write-Host "[OK] gradle.properties updated" -ForegroundColor Green

# 3. local.properties (Android Studio alternative)
"jdk.dir=$JDK17" | Out-File local.properties -Encoding ASCII
Write-Host "[OK] local.properties updated" -ForegroundColor Green

# 4. Patch gradlew.bat to remove JDK 25 usage
$gradlew = "gradlew.bat"
if (Test-Path $gradlew) {
    $content = Get-Content $gradlew -Raw
    $content = $content -replace 'SET "JAVA_EXE=.*"', "SET `"JAVA_EXE=$JDK17\bin\java.exe`""
    $content = $content -replace 'SET JAVA_EXE=.*', "SET `"JAVA_EXE=$JDK17\bin\java.exe`""
    Set-Content $gradlew -Value $content -NoNewline
    Write-Host "[OK] gradlew.bat patched to use JDK 17" -ForegroundColor Green
} else {
    Write-Host "WARNING: gradlew.bat not found — cannot patch" -ForegroundColor Yellow
}

# 5. Remove ALL Gradle cache using wrong Java
Write-Host "[OK] Clearing Gradle cache" -ForegroundColor Green
$gradleCache = "$env:USERPROFILE\.gradle\caches"
if (Test-Path $gradleCache) {
    Remove-Item $gradleCache -Recurse -Force -ErrorAction SilentlyContinue
    Write-Host "[OK] Gradle cache cleared" -ForegroundColor Green
} else {
    Write-Host "[OK] No Gradle cache found to clear" -ForegroundColor Gray
}

# 6. Clean build
Write-Host "`n=== Running CLEAN BUILD ===" -ForegroundColor Yellow
$env:JAVA_HOME = $JDK17
$env:PATH = "$JDK17\bin;$env:PATH"
.\gradlew.bat clean --no-daemon
if ($LASTEXITCODE -ne 0) {
    Write-Host "WARNING: Clean had issues, but continuing..." -ForegroundColor Yellow
}

# 7. Build APK
Write-Host "`n=== BUILDING APK (5-10 minutes) ===" -ForegroundColor Yellow
Write-Host "Please wait, this may take a while...`n" -ForegroundColor Gray
$env:JAVA_HOME = $JDK17
$env:PATH = "$JDK17\bin;$env:PATH"
.\gradlew.bat assembleDebug --no-daemon

# 8. Check result
Write-Host "`n=== Build Result ===" -ForegroundColor Cyan
$apkPath = "app\build\outputs\apk\debug\app-debug.apk"

if (Test-Path $apkPath) {
    Write-Host ""
    Write-Host "========================================" -ForegroundColor Green
    Write-Host "[SUCCESS] APK BUILT!" -ForegroundColor Green
    Write-Host "========================================" -ForegroundColor Green
    $fullPath = Resolve-Path $apkPath
    Write-Host "APK ready at:" -ForegroundColor Cyan
    Write-Host $fullPath -ForegroundColor White
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

