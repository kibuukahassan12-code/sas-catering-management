!include "MUI2.nsh"
!define APPNAME "SAS Management System"
!define COMPANY "SAS Best Foods"
!define VERSION "1.0"

Name "${APPNAME}"
OutFile "SAS_Installer.exe"
InstallDir "$PROGRAMFILES64\SAS Management System"

Page directory
Page instfiles

Section "Install"
    SetOutPath "$INSTDIR"
    File "dist\SAS Management System.exe"
    CreateShortcut "$DESKTOP\SAS Management System.lnk" "$INSTDIR\SAS Management System.exe"
    CreateShortcut "$SMPROGRAMS\SAS Management System\SAS.lnk" "$INSTDIR\SAS Management System.exe"
SectionEnd

Section "Uninstall"
    Delete "$INSTDIR\SAS Management System.exe"
    RMDir /r "$INSTDIR"
SectionEnd

