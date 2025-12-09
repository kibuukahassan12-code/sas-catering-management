$Base = "C:\Users\DELL\Desktop\sas management system"
$Inno = "$Base\installer"
$ISS  = "$Inno\SAS_Installer.iss"

# Ensure installer folder exists
New-Item -ItemType Directory -Force -Path $Inno | Out-Null

# Create .ico file from PNG (Inno requires .ico)
$IconPng = "$Base\sas_logo.png"
$IconIco = "$Inno\sas_logo.ico"

# Use ImageMagick if available, otherwise use System.Drawing with proper ICO creation
$magick = Get-Command magick -ErrorAction SilentlyContinue
if ($magick) {
    & magick convert $IconPng -define icon:auto-resize=256,128,64,48,32,16 $IconIco
} else {
    # Fallback: Create ICO using System.Drawing (simpler method)
    Add-Type -AssemblyName System.Drawing
    $img = [System.Drawing.Image]::FromFile($IconPng)
    $ico = New-Object System.Drawing.Icon($img.GetHicon())
    $fs = New-Object IO.FileStream($IconIco, [IO.FileMode]::Create)
    $ico.Save($fs)
    $fs.Close()
    $ico.Dispose()
    $img.Dispose()
}

# Generate SAS Installer Script
@"
[Setup]
AppName=SAS Management System
AppVersion=1.0
DefaultDirName={pf}\SAS Management System
DefaultGroupName=SAS Management System
OutputDir=$Inno
OutputBaseFilename=SAS_Installer
SetupIconFile=$IconIco
Compression=lzma2
SolidCompression=yes

[Files]
Source: "$Base\dist\app.exe"; DestDir: "{app}"; Flags: ignoreversion
Source: "$Base\dist\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\SAS Management System"; Filename: "{app}\app.exe"; IconFilename: "$IconIco"
Name: "{commondesktop}\SAS Management System"; Filename: "{app}\app.exe"; IconFilename: "$IconIco"

[Run]
Filename: "{app}\app.exe"; Description: "Run SAS Management System"; Flags: nowait postinstall skipifsilent
"@ | Set-Content -Path $ISS -Encoding utf8

# BUILD INSTALLER
& "C:\Program Files (x86)\Inno Setup 6\ISCC.exe" $ISS

Write-Host "`n============================="
Write-Host "✔ Installer Built Successfully!"
Write-Host "✔ Location:"
Write-Host "$Inno\SAS_Installer.exe"
Write-Host "============================="

# === Create GitHub Pages update folder structure ===
$updateDir = 'C:\sas_update_server'
$installer = "$Inno\SAS_Installer.exe"

if (!(Test-Path $updateDir)) { 
    New-Item -ItemType Directory -Path $updateDir | Out-Null 
}

Copy-Item $installer $updateDir -Force

$updateJson = @{
    latest_version = '1.0.0'
    download_url   = 'https://kibuukahassan12-code.github.io/sas-update-server/SAS_Installer.exe'
    release_notes  = 'Auto-update enabled release.'
} | ConvertTo-Json -Depth 10

Set-Content -Path (Join-Path $updateDir 'update.json') -Value $updateJson -Encoding UTF8

Write-Host "`n============================================="
Write-Host "UPDATE SERVER FILES READY"
Write-Host "Upload these two files to your GitHub repo:"
Write-Host "   sas-update-server/update.json"
Write-Host "   sas-update-server/SAS_Installer.exe"
Write-Host "GitHub Pages URL:"
Write-Host "   https://kibuukahassan12-code.github.io/sas-update-server/update.json"
Write-Host "============================================="

Start-Process $updateDir