$iss = 'C:\Users\DELL\Desktop\sas management system\installer\SAS_Installer.iss'
$iscc = 'C:\Program Files (x86)\Inno Setup 6\ISCC.exe'

if (-Not (Test-Path $iscc)) { $iscc = 'C:\Program Files\Inno Setup 6\ISCC.exe' }

if (-Not (Test-Path $iscc)) { 
    Write-Host '❌ Inno Setup compiler not found.' 
    exit 
}

Write-Host '🔧 Building SAS Installer...'
& $iscc $iss

Write-Host '✅ DONE! Your installer is ready.'
Write-Host '📦 Output folder: C:\Users\DELL\Desktop\sas management system\installer'

