Write-Host '=== Building SAS Installer (with Auto-Updater) ==='

$ISCC = 'C:\Program Files (x86)\Inno Setup 6\ISCC.exe'
$ISS  = 'C:\Users\DELL\Desktop\sas management system\installer\SAS_Installer.iss'

if (!(Test-Path $ISCC)) { Write-Error 'ISCC.exe not found!'; exit 1 }
if (!(Test-Path $ISS))  { Write-Error 'SAS_Installer.iss not found!'; exit 1 }

& $ISCC $ISS

Write-Host '=== DONE! Installer built successfully ==='
Write-Host 'Location: C:\Users\DELL\Desktop\sas management system\installer\SAS_Installer.exe'
