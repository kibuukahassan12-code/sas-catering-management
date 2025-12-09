$PY = "C:\Users\DELL\AppData\Local\Programs\Python\Python312\python.exe"
$LOGO = "C:\Users\DELL\Desktop\sas management system\sas_logo.png"
$BASE = "C:\Users\DELL\Desktop\sas management system"

Set-Location $BASE

Write-Host "=== Creating Android project ==="
& $PY -m briefcase create android --no-input
if ($LASTEXITCODE -ne 0) { Write-Host "CREATE FAILED"; exit }

Write-Host "=== Copying SAS logo ==="
$RES = "$BASE\build\sas_management\android\gradle\app\src\main\res"

$mipmaps = "mipmap-mdpi","mipmap-hdpi","mipmap-xhdpi","mipmap-xxhdpi","mipmap-xxxhdpi"
foreach ($m in $mipmaps) {
    $folder = Join-Path $RES $m
    if (!(Test-Path $folder)) { New-Item -ItemType Directory -Path $folder | Out-Null }
    Copy-Item $LOGO (Join-Path $folder "ic_launcher.png") -Force
}

Write-Host "=== Building APK ==="
& $PY -m briefcase build android
if ($LASTEXITCODE -ne 0) { Write-Host "BUILD FAILED"; exit }

Write-Host "=== Packaging APK ==="
& $PY -m briefcase package android
if ($LASTEXITCODE -ne 0) { Write-Host "PACKAGE FAILED"; exit }

$APK = "$BASE\build\sas_management\android\gradle\app\build\outputs\apk\debug\app-debug.apk"

Write-Host ""
Write-Host "================ APK READY ================"
Write-Host "APK Location: $APK"
Write-Host "==========================================="
