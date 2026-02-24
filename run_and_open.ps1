# Start SAS Management server and open browser
Set-Location $PSScriptRoot
Start-Process python -ArgumentList "-m", "sas_management" -NoNewWindow
Start-Sleep -Seconds 6
Start-Process "http://127.0.0.1:5000"
Write-Host "Server starting. Browser opened at http://127.0.0.1:5000"
Write-Host "To stop the server, close the terminal or press Ctrl+C in the server window."
