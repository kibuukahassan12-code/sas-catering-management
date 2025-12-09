$PY='C:\Users\DELL\AppData\Local\Programs\Python\Python312\python.exe'
$LOGO='sas_management\static\images\ssas_logo.png'

Set-Location -Path 'C:\Users\DELL\Desktop\sas management system'

# Clean existing build if present
if (Test-Path 'build\sas_management\android') {
    Write-Host "Removing existing Android build..."
    Remove-Item -Recurse -Force 'build\sas_management\android' -ErrorAction SilentlyContinue
}

# 1) create android project non-interactively (will write into build\sas_management\android\gradle)
& $PY -m briefcase create android --no-input
if ($LASTEXITCODE -ne 0) { Write-Host "Error creating project"; exit 1 }

# 2) copy the provided logo into the Android mipmap folders (create folders if missing)
$destBase = Join-Path -Path (Get-Location) -ChildPath 'build\sas_management\android\gradle\app\src\main\res'

@('mipmap-mdpi','mipmap-hdpi','mipmap-xhdpi','mipmap-xxhdpi','mipmap-xxxhdpi') | ForEach-Object {
    $d=Join-Path $destBase $_
    if(-not (Test-Path $d)){ 
        New-Item -ItemType Directory -Path $d -Force | Out-Null 
    }
    if(Test-Path $LOGO) {
        Copy-Item -Path $LOGO -Destination (Join-Path $d 'ic_launcher.png') -Force -ErrorAction SilentlyContinue
    }
}

# 3) build + package (this runs gradle wrapper or downloads gradle if needed)
& $PY -m briefcase build android
if ($LASTEXITCODE -ne 0) { Write-Host "Error building"; exit 2 }

& $PY -m briefcase package android
if ($LASTEXITCODE -ne 0) { Write-Host "Error packaging"; exit 3 }

Write-Host "`nAPK build complete. APK should be at:"
Write-Host (Join-Path (Get-Location) 'build\sas_management\android\gradle\app\build\outputs\apk\debug\app-debug.apk')

