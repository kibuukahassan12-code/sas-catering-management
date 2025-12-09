Write-Host ""
Write-Host "============================================="
Write-Host "        SAS MANAGEMENT APK BUILD WIZARD       "
Write-Host "============================================="

$PY = "C:\Users\DELL\AppData\Local\Programs\Python\Python312\python.exe"
$LOGO = "C:\Users\DELL\Desktop\sas management system\sas_logo.png"
$BASE = Get-Location

Write-Host ""
Write-Host "Python path: $PY"
Write-Host "Logo path:   $LOGO"
Write-Host ""

function Pause-Step {
    Write-Host ""
    Read-Host "Press ENTER to continue..."
}

Write-Host ""
Write-Host "STEP 1 - Creating Android project..."
Write-Host "---------------------------------------------"
& $PY -m briefcase create android
Pause-Step

Write-Host ""
Write-Host "STEP 2 - Copying SAS Logo to mipmap folders..."
Write-Host "---------------------------------------------"

$resPath = Join-Path $BASE "build\sas_management\android\gradle\app\src\main\res"
$folders = @("mipmap-mdpi","mipmap-hdpi","mipmap-xhdpi","mipmap-xxhdpi","mipmap-xxxhdpi")

foreach ($f in $folders) {
    $dest = Join-Path $resPath $f
    if (-not (Test-Path $dest)) {
        New-Item -ItemType Directory -Path $dest | Out-Null
    }
    Copy-Item -Path $LOGO -Destination (Join-Path $dest "ic_launcher.png") -Force
    Write-Host "Logo added to $f"
}

Pause-Step

Write-Host ""
Write-Host "STEP 3 - Building APK (This may take minutes)..."
Write-Host "---------------------------------------------"

& $PY -m briefcase build android
Pause-Step

Write-Host ""
Write-Host "STEP 4 - Packaging APK..."
Write-Host "---------------------------------------------"

& $PY -m briefcase package android

$APK = Join-Path $BASE "build\sas_management\android\gradle\app\build\outputs\apk\debug\app-debug.apk"

Write-Host ""
Write-Host "============================================="
Write-Host "               BUILD COMPLETE!"
Write-Host "============================================="
Write-Host "APK Location:"
Write-Host "   $APK"
Write-Host "============================================="
Write-Host ""

Pause-Step

