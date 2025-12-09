[Setup]
AppName=SAS Management System
AppVersion=1.0
DefaultDirName={pf}\SAS Management System
DefaultGroupName=SAS Management System
OutputBaseFilename=SAS_Installer
Compression=lzma
SolidCompression=yes

[Files]
Source: "dist\app_launcher.exe"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{group}\SAS Management System"; Filename: "{app}\app_launcher.exe"
Name: "{commondesktop}\SAS Management System"; Filename: "{app}\app_launcher.exe"; Tasks: desktopicon

[Tasks]
Name: "desktopicon"; Description: "Create a desktop icon"; GroupDescription: "Additional icons:"

