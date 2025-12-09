$Base = 'C:\Users\DELL\Desktop\sas management system'
$ISCC = 'C:\Program Files (x86)\Inno Setup 6\ISCC.exe'
$ISS  = Join-Path $Base 'installer\SAS_Installer.iss'
$Dist = Join-Path $Base 'dist'

Write-Host '=== Checking updater.exe ==='
if (!(Test-Path (Join-Path $Dist 'updater.exe'))) {
    Write-Host 'Updater.exe missing — building now...'
    python $Base\updater.py
}

Write-Host '=== Ensuring logo icon exists in dist ==='
Copy-Item -Path (Join-Path $Base 'sas_logo.ico') -Destination (Join-Path $Dist 'sas_logo.ico') -Force

Write-Host '=== Building SAS Installer silently ==='
& $ISCC $ISS

Write-Host '=== DONE! ==='
Write-Host 'Installer created at:  C:\Users\DELL\Desktop\sas management system\installer\SAS_Installer.exe'

