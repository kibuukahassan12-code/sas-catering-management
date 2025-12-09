[Setup]
AppName=SAS Management System
AppVersion=1.0
DefaultDirName={pf}\SAS Management System
DefaultGroupName=SAS Management System
OutputDir=C:\Users\DELL\Desktop\sas management system\installer
OutputBaseFilename=SAS_Installer
SetupIconFile=C:\Users\DELL\Desktop\sas management system\dist\sas_logo.ico
Compression=lzma2
SolidCompression=yes

[Files]
Source: "C:\Users\DELL\Desktop\sas management system\dist\app.exe"; DestDir: "{app}"; Flags: ignoreversion
Source: "C:\Users\DELL\Desktop\sas management system\dist\sas_logo.ico"; DestDir: "{app}"; Flags: ignoreversion
Source: "C:\Users\DELL\Desktop\sas management system\dist\updater.exe"; DestDir: "{app}"; Flags: ignoreversion
Source: "C:\Users\DELL\Desktop\sas management system\dist\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\SAS Management System"; Filename: "{app}\app.exe"; IconFilename: "{app}\sas_logo.ico"
Name: "{commondesktop}\SAS Management System"; Filename: "{app}\app.exe"; WorkingDir: "{app}"; IconFilename: "{app}\sas_logo.ico"

[Run]
Filename: "{app}\app.exe"; Description: "Run SAS Management System"; Flags: nowait postinstall skipifsilent
Filename: "{app}\updater.exe"; Flags: nowait runhidden

