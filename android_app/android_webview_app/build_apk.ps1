$ErrorActionPreference = "Stop"

$root = Split-Path -Parent $MyInvocation.MyCommand.Path
$logoSource = Join-Path (Split-Path -Parent (Split-Path -Parent $root)) "sas_logo.png"

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "SAS Android WebView App - Build Script" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Change to project directory
Set-Location $root
Write-Host "Working directory: $root" -ForegroundColor Yellow
Write-Host ""

# 1) Copy logo to all mipmap folders
$resBase = Join-Path $root "app\src\main\res"
$mipmaps = @('mipmap-mdpi','mipmap-hdpi','mipmap-xhdpi','mipmap-xxhdpi','mipmap-xxxhdpi')

if (Test-Path $logoSource) {
    Write-Host "Copying logo to mipmap folders..." -ForegroundColor Yellow
    foreach ($m in $mipmaps) {
        $destDir = Join-Path $resBase $m
        if (-not (Test-Path $destDir)) { 
            New-Item -ItemType Directory -Path $destDir -Force | Out-Null 
        }
        $destFile = Join-Path $destDir 'ic_launcher.png'
        try {
            if (Test-Path $destFile) { 
                $file = Get-Item $destFile
                $file.Attributes = $file.Attributes -band (-bnot [System.IO.FileAttributes]::ReadOnly)
            }
            Copy-Item -Path $logoSource -Destination $destFile -Force -ErrorAction Stop
            Write-Host "  ✓ Copied to $m" -ForegroundColor Green
        } catch {
            Write-Warning "  ✗ Failed to copy to $m : $($_.Exception.Message)"
        }
    }
    Write-Host ""
} else { 
    Write-Warning "Logo source not found: $logoSource"
    Write-Warning "Continuing without logo copy..."
    Write-Host ""
}

# 2) Verify and setup Gradle wrapper
$wrapperJar = Join-Path $root "gradle\wrapper\gradle-wrapper.jar"
if (-not (Test-Path $wrapperJar)) {
    Write-Host "Gradle wrapper JAR not found. Attempting to download..." -ForegroundColor Yellow
    $gradleVersion = "8.5"
    $wrapperUrl = "https://raw.githubusercontent.com/gradle/gradle/v$gradleVersion/gradle/wrapper/gradle-wrapper.jar"
    
    try {
        $wrapperDir = Split-Path $wrapperJar
        if (-not (Test-Path $wrapperDir)) {
            New-Item -ItemType Directory -Path $wrapperDir -Force | Out-Null
        }
        Invoke-WebRequest -Uri $wrapperUrl -OutFile $wrapperJar -UseBasicParsing
        Write-Host "✓ Gradle wrapper JAR downloaded" -ForegroundColor Green
    } catch {
        Write-Warning "Failed to download wrapper JAR automatically."
        Write-Warning "Please ensure gradle/wrapper/gradle-wrapper.jar exists"
        Write-Warning "Or run: gradle wrapper"
    }
    Write-Host ""
}

$gradlew = Join-Path $root "gradlew.bat"
if (-not (Test-Path $gradlew)) {
    Write-Error "gradlew.bat not found at: $gradlew"
    Write-Error "Please ensure the Gradle wrapper is properly set up."
    exit 1
}

# 3) Clean and build
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Building APK (this may take several minutes)..." -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Clean first
Write-Host "Running: gradlew clean" -ForegroundColor Yellow
& $gradlew clean --no-daemon
if ($LASTEXITCODE -ne 0) {
    Write-Error "Gradle clean failed with exit code $LASTEXITCODE"
    exit $LASTEXITCODE
}

Write-Host ""
Write-Host "Running: gradlew assembleDebug" -ForegroundColor Yellow
& $gradlew assembleDebug --no-daemon

$exitCode = $LASTEXITCODE
if ($exitCode -ne 0) {
    Write-Error "Gradle build failed with exit code $exitCode"
    Write-Error "Please check the error messages above."
    exit $exitCode
}

# 4) Check for APK
$apk = Join-Path $root "app\build\outputs\apk\debug\app-debug.apk"

if (Test-Path $apk) {
    Write-Host ""
    Write-Host "========================================" -ForegroundColor Green
    Write-Host "✓ BUILD SUCCESS!" -ForegroundColor Green
    Write-Host "========================================" -ForegroundColor Green
    Write-Host ""
    Write-Host "APK READY: app/build/outputs/apk/debug/app-debug.apk" -ForegroundColor Green
    Write-Host "Full path: $apk" -ForegroundColor Green
    Write-Host ""
    
    # Open the APK folder
    $apkFolder = Split-Path $apk
    Start-Process explorer.exe -ArgumentList $apkFolder
    
    exit 0
} else {
    Write-Error "Build completed but APK not found at expected location: $apk"
    Write-Error "Please check the build output for errors."
    exit 1
}


