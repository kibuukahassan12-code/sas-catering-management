# Error-free Android APK Build Script
# Ensures JDK 17 is used and all prerequisites are met

$project = Split-Path -Parent $MyInvocation.MyCommand.Path;
Set-Location $project;

Write-Host "=== Android APK Build Script (Error-Free) ===" -ForegroundColor Cyan
Write-Host "Project: $project`n" -ForegroundColor Gray

# Step 1: Ensure JDK 17 is set
Write-Host "=== Step 1: Configuring JDK 17 ===" -ForegroundColor Yellow

$JDK17Path = "C:\Program Files\Java\jdk-17"
$JDK17Adoptium = Get-ChildItem "C:\Program Files\Eclipse Adoptium\jdk-17*" -ErrorAction SilentlyContinue | Select-Object -First 1 -ExpandProperty FullName

if (Test-Path $JDK17Path) {
    $JDK17 = $JDK17Path
} elseif ($JDK17Adoptium) {
    $JDK17 = $JDK17Adoptium
} else {
    Write-Host "ERROR: JDK 17 not found!" -ForegroundColor Red
    Write-Host "Please install JDK 17 or run setup_jdk17.ps1 first." -ForegroundColor Red
    exit 1
}

# Set JAVA_HOME for this session
$env:JAVA_HOME = $JDK17
$env:PATH = "$JDK17\bin;$env:PATH"

Write-Host "[OK] JAVA_HOME: $env:JAVA_HOME" -ForegroundColor Green
Write-Host "Java version:" -ForegroundColor Gray
& "$JDK17\bin\java.exe" -version 2>&1 | Select-Object -First 3

# Step 2: Ensure gradlew exists
Write-Host "`n=== Step 2: Ensuring gradlew exists ===" -ForegroundColor Yellow

if (-not(Test-Path 'gradlew.bat')) {
    Write-Host 'Creating gradlew wrapper...' -ForegroundColor Yellow
    & "$JDK17\bin\java.exe" -classpath 'gradle/wrapper/gradle-wrapper.jar' org.gradle.wrapper.GradleWrapperMain
    if ($LASTEXITCODE -ne 0) { 
        Write-Host "ERROR: Failed to create gradlew wrapper" -ForegroundColor Red
        exit 1 
    }
    Write-Host "[OK] gradlew.bat created" -ForegroundColor Green
} else {
    Write-Host "[OK] gradlew.bat exists" -ForegroundColor Green
}

# Step 3: Ensure Android icon exists
Write-Host "`n=== Step 3: Ensuring Android icon exists ===" -ForegroundColor Yellow

$mip = Join-Path $project 'app/src/main/res';
$iconPath = Join-Path (Split-Path -Parent (Split-Path -Parent $project)) 'sas_logo.png';

if (-not(Test-Path $iconPath)) {
    Write-Host "WARNING: Icon not found at $iconPath" -ForegroundColor Yellow
    Write-Host "Skipping icon copy..." -ForegroundColor Yellow
} else {
    $targets = @('mipmap-mdpi','mipmap-hdpi','mipmap-xhdpi','mipmap-xxhdpi','mipmap-xxxhdpi');
    
    foreach ($t in $targets) {
        $d = Join-Path $mip $t;
        if (-not(Test-Path $d)) { 
            New-Item -ItemType Directory -Path $d -Force | Out-Null 
        }
        $targetIcon = Join-Path $d 'ic_launcher.png'
        # Remove read-only attribute if it exists
        if (Test-Path $targetIcon) {
            Set-ItemProperty -Path $targetIcon -Name IsReadOnly -Value $false -ErrorAction SilentlyContinue
        }
        Copy-Item $iconPath $targetIcon -Force -ErrorAction SilentlyContinue
    }
    Write-Host "[OK] Icons copied to all mipmap directories" -ForegroundColor Green
}

# Step 4: Clean build
Write-Host "`n=== Step 4: Cleaning build ===" -ForegroundColor Yellow
# Set JAVA_HOME with proper escaping for batch files
$env:JAVA_HOME = $JDK17
$env:PATH = "$JDK17\bin;$env:PATH"

# Use wrapper batch file that properly handles paths with spaces
if (Test-Path "gradlew_jdk17.bat") {
    & ".\gradlew_jdk17.bat" clean --no-daemon
} else {
    & ".\gradlew.bat" clean --no-daemon
}
if ($LASTEXITCODE -ne 0) {
    Write-Host "WARNING: Clean build had issues, but continuing..." -ForegroundColor Yellow
}

# Step 5: Build APK
Write-Host "`n=== Step 5: Building APK (5-10 minutes) ===" -ForegroundColor Yellow
Write-Host "This may take a while, please be patient...`n" -ForegroundColor Gray

# Ensure JAVA_HOME is set again (in case it was cleared)
$env:JAVA_HOME = $JDK17
$env:PATH = "$JDK17\bin;$env:PATH"

# Use wrapper batch file that properly handles paths with spaces
if (Test-Path "gradlew_jdk17.bat") {
    & ".\gradlew_jdk17.bat" assembleDebug --no-daemon
} else {
    & ".\gradlew.bat" assembleDebug --no-daemon
}

# Step 6: Check result
Write-Host "`n=== Build Result ===" -ForegroundColor Cyan

$apk = Join-Path $project 'app/build/outputs/apk/debug/app-debug.apk';

if (Test-Path $apk) {
    Write-Host ""
    Write-Host "========================================" -ForegroundColor Green
    Write-Host "[SUCCESS] APK BUILT" -ForegroundColor Green
    Write-Host "========================================" -ForegroundColor Green
    Write-Host "APK Location:" -ForegroundColor Cyan
    Write-Host "  $apk" -ForegroundColor White
    
    $apkInfo = Get-Item $apk
    Write-Host "`nFile Size: $([math]::Round($apkInfo.Length / 1MB, 2)) MB" -ForegroundColor Gray
    Write-Host "Created: $($apkInfo.CreationTime)" -ForegroundColor Gray
} else {
    Write-Host ""
    Write-Host "========================================" -ForegroundColor Red
    Write-Host "[FAILED] BUILD FAILED" -ForegroundColor Red
    Write-Host "========================================" -ForegroundColor Red
    Write-Host "APK not found at: $apk" -ForegroundColor Yellow
    Write-Host "Please check the terminal output above for errors." -ForegroundColor Yellow
    exit 1
}

Write-Host ""

