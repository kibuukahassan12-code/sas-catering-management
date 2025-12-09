# Check APK Build Result
$apk = "app\build\outputs\apk\debug\app-debug.apk"

if (Test-Path $apk) {
    $fullPath = (Resolve-Path $apk).Path
    $size = (Get-Item $apk).Length / 1MB
    
    Write-Host "`n=============================================" -ForegroundColor Green
    Write-Host "  APK BUILT SUCCESSFULLY 🎉" -ForegroundColor Green
    Write-Host "=============================================" -ForegroundColor Green
    Write-Host "LOCATION: $fullPath" -ForegroundColor Cyan
    Write-Host "SIZE: $([math]::Round($size, 2)) MB" -ForegroundColor Cyan
    Write-Host "=============================================" -ForegroundColor Green
    
    # Open folder
    Start-Process explorer.exe -ArgumentList "/select,`"$fullPath`""
} else {
    Write-Host "`n❌ BUILD FAILED — APK NOT FOUND" -ForegroundColor Red
    Write-Host "Expected location: $apk" -ForegroundColor Yellow
    Write-Host "`nPlease check the build output for errors." -ForegroundColor Yellow
}

