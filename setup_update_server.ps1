# === Create GitHub Pages update folder structure ===
mkdir "C:\sas_update_server" -Force
Set-Location "C:\sas_update_server"

# Copy your latest installer to update server folder
Copy-Item "C:\Users\DELL\Desktop\sas management system\installer\SAS_Installer.exe" -Destination ".\" -Force

# Create update.json for GitHub Pages
@"
{
  "latest_version": "1.0.0",
  "download_url": "https://YOUR_GITHUB_USERNAME.github.io/sas-update-server/SAS_Installer.exe",
  "release_notes": "Initial release with auto-updater system."
}
"@ | Out-File -Encoding UTF8 "update.json"

Write-Host "`n=== Upload the contents of C:\sas_update_server to your GitHub repo sas-update-server and enable GitHub Pages ==="
Write-Host "Files created:"
Get-ChildItem "C:\sas_update_server" | Select-Object Name, Length

Set-Location "C:\Users\DELL\Desktop\sas management system"

