$ISCC = 'C:\Program Files (x86)\Inno Setup 6\ISCC.exe'
$ISS = 'C:\Users\DELL\Desktop\sas management system\installer\SAS_Installer.iss'

Write-Host '📦 Building SAS Installer...'

& $ISCC $ISS

Write-Host '✅ DONE! Check installer folder for SAS_Installer.exe'

