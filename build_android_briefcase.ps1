# ================================
# ANDROID APK BUILDER USING BRIEFCASE
# Uses Python Briefcase to package the SAS Management System
# ================================

$PY = 'C:\Users\DELL\AppData\Local\Programs\Python\Python312\python.exe'
$PROJECT = 'C:\Users\DELL\Desktop\sas management system'
$LOGO = Join-Path $PROJECT 'sas_logo.png'

Set-Location $PROJECT

Write-Host '=== 1) Create Android project (Briefcase) ==='

& $PY -m briefcase create android --no-input

if ($LASTEXITCODE -ne 0) { 
    Write-Error 'Briefcase create failed. See output above.'
    exit 1 
}

Write-Host '=== 2) Copy SAS logo into mipmap folders ==='

$dest = Join-Path $PROJECT 'build\sas_management\android\gradle\app\src\main\res'

$mips = @('mipmap-mdpi','mipmap-hdpi','mipmap-xhdpi','mipmap-xxhdpi','mipmap-xxxhdpi')

foreach ($m in $mips) {
    $d = Join-Path $dest $m
    
    if (-not (Test-Path $d)) { 
        New-Item -ItemType Directory -Path $d | Out-Null 
    }
    
    if (-not (Test-Path $LOGO)) { 
        Write-Error "Logo not found at: $LOGO"
        exit 2 
    }
    
    Copy-Item -Path $LOGO -Destination (Join-Path $d 'ic_launcher.png') -Force
}

Write-Host '=== 3) Build APK (this will take several minutes) ==='

& $PY -m briefcase build android

if ($LASTEXITCODE -ne 0) { 
    Write-Error 'Briefcase build failed. See output above.'
    exit 3 
}

Write-Host '=== 4) Package APK ==='

& $PY -m briefcase package android

if ($LASTEXITCODE -ne 0) { 
    Write-Error 'Briefcase package failed. See output above.'
    exit 4 
}

$apk = Join-Path $PROJECT 'build\sas_management\android\gradle\app\build\outputs\apk\debug\app-debug.apk'

if (Test-Path $apk) {
    Write-Host ''
    Write-Host '================ APK READY ================'
    Write-Host "APK Location: $apk"
    Write-Host '=========================================='
} else {
    Write-Error "APK not found at expected location: $apk"
    exit 5
}

