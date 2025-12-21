$project = 'C:/Users/DELL/Desktop/sas management system/android_app/android_webview_app';

Set-Location $project;

Write-Host '=== FIX 1: Ensure gradlew exists ===';
if (-not(Test-Path 'gradlew.bat')) {
    Write-Host 'gradlew.bat not found - checking if we can create it...';
    $wrapperJar = Join-Path $project 'gradle/wrapper/gradle-wrapper.jar';
    if (Test-Path $wrapperJar) {
        Write-Host 'Creating gradlew.bat...';
        $gradlewContent = @'
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
'@
        Set-Content -Path (Join-Path $project 'gradlew.bat') -Value $gradlewContent -Encoding ASCII
        Write-Host 'gradlew.bat created';
    } else {
        Write-Host 'ERROR: gradle-wrapper.jar not found. Cannot create gradlew.bat';
        exit 1;
    }
} else {
    Write-Host 'gradlew.bat already exists';
}

Write-Host '=== FIX 2: Ensure Android icon exists ===';
$mip = Join-Path $project 'app/src/main/res';
$icon = Join-Path (Split-Path -Parent (Split-Path -Parent $project)) 'sas_logo.png';
$targets = @('mipmap-mdpi','mipmap-hdpi','mipmap-xhdpi','mipmap-xxhdpi','mipmap-xxxhdpi');

if (-not (Test-Path $icon)) {
    Write-Host "WARNING: Logo not found at $icon" -ForegroundColor Yellow;
    Write-Host "Continuing without logo copy...";
} else {
    foreach ($t in $targets) {
        $d = Join-Path $mip $t;
        if (-not(Test-Path $d)) { 
            New-Item -ItemType Directory $d -Force | Out-Null 
        }
        $dest = Join-Path $d 'ic_launcher.png';
        try {
            if (Test-Path $dest) {
                $file = Get-Item $dest;
                $file.Attributes = $file.Attributes -band (-bnot [System.IO.FileAttributes]::ReadOnly);
            }
            Copy-Item $icon $dest -Force -ErrorAction Stop;
            Write-Host "  Copied logo to $t" -ForegroundColor Green;
        } catch {
            Write-Warning "  Failed to copy to $t : $($_.Exception.Message)";
        }
    }
}

Write-Host '=== FIX 3: Clean build ===';
./gradlew.bat clean --no-daemon
if ($LASTEXITCODE -ne 0) {
    Write-Host 'Clean failed!' -ForegroundColor Red;
    exit $LASTEXITCODE;
}

Write-Host '=== BUILDING APK - PLEASE WAIT 5-10 MINUTES ===' -ForegroundColor Cyan;
./gradlew.bat assembleDebug --no-daemon

$exitCode = $LASTEXITCODE;
$apk = Join-Path $project 'app/build/outputs/apk/debug/app-debug.apk';

if ($exitCode -eq 0 -and (Test-Path $apk)) {
    Write-Host '';
    Write-Host '=== SUCCESS! APK BUILT ===' -ForegroundColor Green;
    Write-Host "APK Location: $apk" -ForegroundColor Green;
    Write-Host '';
    Start-Process explorer.exe -ArgumentList (Split-Path $apk);
} else {
    Write-Host '';
    Write-Host 'BUILD FAILED - CHECK TERMINAL OUTPUT.' -ForegroundColor Red;
    if ($exitCode -ne 0) {
        Write-Host "Exit code: $exitCode" -ForegroundColor Red;
    }
    exit 1;
}
























