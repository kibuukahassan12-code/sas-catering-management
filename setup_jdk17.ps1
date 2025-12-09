# FIX ANDROID APK BUILD (JDK 25 ERROR)
# -------------------------------------

Write-Host "=== Setting up JDK 17 for Android Build ===" -ForegroundColor Cyan

# Check if JDK 17 exists
$JDK17Path = "C:\Program Files\Java\jdk-17"
$JDK17Adoptium = Get-ChildItem "C:\Program Files\Eclipse Adoptium\jdk-17*" -ErrorAction SilentlyContinue | Select-Object -First 1 -ExpandProperty FullName

if (Test-Path $JDK17Path) {
    $JDK17 = $JDK17Path
    Write-Host "[OK] Found JDK 17 at: $JDK17" -ForegroundColor Green
} elseif ($JDK17Adoptium) {
    $JDK17 = $JDK17Adoptium
    Write-Host "[OK] Found JDK 17 at: $JDK17" -ForegroundColor Green
} else {
    Write-Host "JDK 17 not found. Installing..." -ForegroundColor Yellow
    Write-Host "Installing JDK 17 (Adoptium)..." -ForegroundColor Yellow
    winget install --silent EclipseAdoptium.Temurin.17.JDK
    
    # Wait a moment for installation
    Start-Sleep -Seconds 5
    
    $JDK17 = Get-ChildItem "C:\Program Files\Eclipse Adoptium\jdk-17*" | Select-Object -First 1 -ExpandProperty FullName
    if (-not $JDK17) {
        Write-Host "ERROR: JDK 17 installation failed or path not found." -ForegroundColor Red
        exit 1
    }
    Write-Host "[OK] JDK 17 installed at: $JDK17" -ForegroundColor Green
}

# Set JAVA_HOME for current session
$env:JAVA_HOME = $JDK17
$env:PATH = "$JDK17\bin;$env:PATH"

Write-Host ""
Write-Host "[OK] JAVA_HOME set for current session: $env:JAVA_HOME" -ForegroundColor Green

# Verify Java version
Write-Host ""
Write-Host "Java version:" -ForegroundColor Cyan
& "$JDK17\bin\java.exe" -version

# Set system-wide JAVA_HOME (requires admin)
Write-Host ""
Write-Host "=== Setting System-Wide JAVA_HOME ===" -ForegroundColor Cyan
Write-Host "Note: This requires administrator privileges." -ForegroundColor Yellow

try {
    # Try to set system-wide JAVA_HOME
    $currentValue = [Environment]::GetEnvironmentVariable("JAVA_HOME", "Machine")
    if ($currentValue -ne $JDK17) {
        Write-Host "Setting JAVA_HOME system-wide..." -ForegroundColor Yellow
        [Environment]::SetEnvironmentVariable("JAVA_HOME", $JDK17, "Machine")
        Write-Host "[OK] JAVA_HOME set system-wide" -ForegroundColor Green
    } else {
        Write-Host "[OK] JAVA_HOME already set correctly" -ForegroundColor Green
    }
    
    # Update PATH to include JDK 17 bin first
    $currentPath = [Environment]::GetEnvironmentVariable("PATH", "Machine")
    $jdkBin = "$JDK17\bin"
    
    if ($currentPath -notlike "*$jdkBin*") {
        Write-Host "Adding JDK 17 to PATH..." -ForegroundColor Yellow
        $newPath = "$jdkBin;$currentPath"
        [Environment]::SetEnvironmentVariable("PATH", $newPath, "Machine")
        Write-Host "[OK] PATH updated" -ForegroundColor Green
    } else {
        Write-Host "[OK] JDK 17 already in PATH" -ForegroundColor Green
    }
} catch {
    Write-Host "WARNING: Could not set system-wide environment variables." -ForegroundColor Yellow
    Write-Host "You may need to run this script as Administrator." -ForegroundColor Yellow
    Write-Host "Error: $_" -ForegroundColor Red
    Write-Host ""
    Write-Host "You can manually set JAVA_HOME using:" -ForegroundColor Yellow
    Write-Host "  setx JAVA_HOME `"$JDK17`" /M" -ForegroundColor Cyan
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "JDK 17 Configuration Complete!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "NOTE: Restart Cursor terminal for system-wide changes to take effect." -ForegroundColor Yellow
Write-Host ""
Write-Host "To build APK, run:" -ForegroundColor Cyan
Write-Host "  cd 'android_app/android_webview_app'" -ForegroundColor White
Write-Host "  powershell -ExecutionPolicy Bypass -File build_apk_error_free.ps1" -ForegroundColor White
Write-Host ""
