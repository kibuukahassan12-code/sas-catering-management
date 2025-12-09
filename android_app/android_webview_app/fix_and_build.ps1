# Fix Android APK build by forcing JDK 17 and repairing Gradle configuration

Write-Host "=== FIXING ANDROID BUILD SYSTEM ===" -ForegroundColor Cyan

# 1. Force-use JDK 17
$JDK17 = "C:\Program Files\Java\jdk-17"

if (!(Test-Path $JDK17)) {
    Write-Host "ERROR: JDK 17 not found. Install from https://adoptium.net/temurin/releases/?version=17" -ForegroundColor Red
    exit 1
}

$Env:JAVA_HOME = $JDK17
try {
    [System.Environment]::SetEnvironmentVariable("JAVA_HOME", $JDK17, "Machine")
    Write-Host "[OK] JAVA_HOME set to JDK 17 (system-wide)" -ForegroundColor Green
} catch {
    Write-Host "[OK] JAVA_HOME set to JDK 17 (current session only)" -ForegroundColor Yellow
    Write-Host "Note: System-wide setting requires admin privileges" -ForegroundColor Gray
}

Write-Host "[OK] JAVA_HOME set to JDK 17" -ForegroundColor Green

# 2. Patch gradlew.bat to use JDK 17
$gradlew = "gradlew.bat"
if (Test-Path $gradlew) {
    $content = Get-Content $gradlew -Raw
    $content = $content -replace 'SET "JAVA_EXE=.*"', "SET `"JAVA_EXE=$JDK17\bin\java.exe`""
    $content = $content -replace 'SET JAVA_EXE=.*', "SET `"JAVA_EXE=$JDK17\bin\java.exe`""
    Set-Content $gradlew -Value $content -NoNewline
    Write-Host "[OK] gradlew.bat patched" -ForegroundColor Green
} else {
    Write-Host "WARNING: gradlew.bat not found" -ForegroundColor Yellow
}

# 3. Patch local.properties
$localProps = "local.properties"
"jdk.dir=$JDK17" | Out-File $localProps -Encoding ASCII
Write-Host "[OK] local.properties updated" -ForegroundColor Green

# 4. Patch gradle.properties
$gradleProps = "gradle.properties"
@"
org.gradle.java.home=$JDK17
android.useAndroidX=true
android.enableJetifier=true
org.gradle.jvmargs=-Xmx2048m -Dfile.encoding=UTF-8
"@ | Out-File $gradleProps -Encoding ASCII
Write-Host "[OK] gradle.properties updated" -ForegroundColor Green

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

# 7. Check result
Write-Host "`n=== Build Result ===" -ForegroundColor Cyan
$apk = "app\build\outputs\apk\debug\app-debug.apk"

if (Test-Path $apk) {
    Write-Host ""
    Write-Host "========================================" -ForegroundColor Green
    Write-Host "[SUCCESS] APK BUILT!" -ForegroundColor Green
    Write-Host "========================================" -ForegroundColor Green
    $apkPath = Resolve-Path $apk
    Write-Host "APK Location: $apkPath" -ForegroundColor White
    $apkInfo = Get-Item $apk
    Write-Host "File Size: $([math]::Round($apkInfo.Length / 1MB, 2)) MB" -ForegroundColor Gray
} else {
    Write-Host ""
    Write-Host "========================================" -ForegroundColor Red
    Write-Host "[FAILED] BUILD FAILED" -ForegroundColor Red
    Write-Host "========================================" -ForegroundColor Red
    Write-Host "APK not found at: $apk" -ForegroundColor Yellow
    Write-Host "Check the output above for errors." -ForegroundColor Yellow
    exit 1
}

Write-Host ""
Write-Host "=== DONE ===" -ForegroundColor Green

