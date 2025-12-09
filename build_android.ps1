$root = 'C:\Users\DELL\Desktop\sas management system\android_app\android_webview_app'

$logoSource = 'C:\Users\DELL\Desktop\sas management system\sas_logo.png'

Write-Host 'Working folder:' $root

if (-not (Test-Path $root)) { 
    Write-Error "Project folder not found: $root"
    exit 2 
}

Set-Location $root

# 1) Make sure gradlew.bat exists (minimal wrapper launcher)
$gradleBat = Join-Path $root 'gradlew.bat'

if (-not (Test-Path $gradleBat)) {
    Write-Host 'gradlew.bat missing - creating a minimal launcher...'
    $content = @'
@echo off
REM Minimal gradle wrapper launcher
SET SCRIPT_DIR=%~dp0
SET WRAPPER_JAR=%SCRIPT_DIR%gradle\wrapper\gradle-wrapper.jar
if exist "%WRAPPER_JAR%" (
  java -jar "%WRAPPER_JAR%" %*
) else (
  echo ERROR: gradle wrapper jar not found at %WRAPPER_JAR%
  exit /b 10
)
'@
    Set-Content -Path $gradleBat -Value $content -Encoding ASCII
    icacls $gradleBat /grant *S-1-1-0:F | Out-Null
    Write-Host 'Created gradlew.bat'
} else { 
    Write-Host 'gradlew.bat already present.' 
}

# 2) Check gradle wrapper jar
$wrapperJar = Join-Path $root 'gradle\wrapper\gradle-wrapper.jar'

if (-not (Test-Path $wrapperJar)) {
    Write-Warning 'gradle-wrapper.jar not found. Gradle wrapper may be incomplete. If build fails, ensure gradle/wrapper/gradle-wrapper.jar exists.'
} else { 
    Write-Host 'gradle-wrapper.jar found.' 
}

# 3) Copy logo to all mipmap folders (clear read-only if needed)
$resBase = Join-Path $root 'app\src\main\res'
$mipmaps = @('mipmap-mdpi','mipmap-hdpi','mipmap-xhdpi','mipmap-xxhdpi','mipmap-xxxhdpi')

if (-not (Test-Path $logoSource)) { 
    Write-Warning "Logo source not found: $logoSource" 
} else {
    foreach ($m in $mipmaps) {
        $destDir = Join-Path $resBase $m
        if (-not (Test-Path $destDir)) { 
            New-Item -ItemType Directory -Path $destDir -Force | Out-Null 
        }
        $destFile = Join-Path $destDir 'ic_launcher.png'
        try {
            if (Test-Path $destFile) { 
                (Get-Item $destFile).Attributes = ((Get-Item $destFile).Attributes -band (-bnot [IO.FileAttributes]::ReadOnly)) 
            }
            Copy-Item -Path $logoSource -Destination $destFile -Force -ErrorAction Stop
            Write-Host "Copied logo -> $destFile"
        } catch {
            Write-Warning "Failed to copy logo to $destFile : $($_.Exception.Message) (continuing)"
        }
    }
}

# 4) Run gradlew assembleDebug
Write-Host '=== Building APK (this can take several minutes) ===' -ForegroundColor Cyan

$gradlewExe = Join-Path $root 'gradlew.bat'

if (-not (Test-Path $gradlewExe)) { 
    Write-Error 'gradlew.bat not present - cannot build.'
    exit 11 
}

& $gradlewExe 'assembleDebug' '--no-daemon'

$exit = $LASTEXITCODE

if ($exit -ne 0) {
    Write-Error "Gradle build failed with exit code $exit. See output above for details."
    exit $exit
}

# 5) Locate APK and open folder
$apk = Join-Path $root 'app\build\outputs\apk\debug\app-debug.apk'

if (Test-Path $apk) {
    Write-Host '=== APK BUILD SUCCESS ===' -ForegroundColor Green
    Write-Host 'APK location:' $apk
    Start-Process explorer.exe (Split-Path $apk)
    exit 0
} else {
    Write-Error "Build reported success but APK not found at expected location: $apk"
    exit 12
}
