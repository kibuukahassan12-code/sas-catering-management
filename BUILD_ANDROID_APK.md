# Building SAS Management System Android APK

This guide explains how to build the Android APK for the SAS Management System.

## Quick Build

Navigate to the Android app directory and run the build script:

```powershell
cd android_app\android_webview_app
.\build_sas_apk.ps1
```

The APK will be generated at: `app\build\outputs\apk\debug\app-debug.apk`

## What's Included

✅ **SAS Logo** - Automatically generated as app icon  
✅ **All Modules** - Complete access to all SAS features  
✅ **SAS Branding** - Consistent UI and branding  
✅ **Mobile Optimized** - Full WebView with native Android features  

## Configuration

### Server URL

Before building, configure your server URL in:
```
android_app\android_webview_app\app\src\main\res\values\strings.xml
```

Change the `server_url` string to your server address:
- **Development**: `http://127.0.0.1:5000` (or your local IP)
- **Production**: `https://your-production-server.com`

### App Name

The app name is set in `strings.xml` as "SAS Management System". You can customize it there.

## Requirements

- Android SDK Platform 34+
- Java JDK 17+
- Python (for icon generation)
- Gradle (included via wrapper)

## Detailed Documentation

See `android_app/android_webview_app/README_SAS_APK.md` for complete documentation.

## Features

The APK provides full access to all SAS Management System modules:
- Dashboard & Analytics
- Event Service Department
- Accounting & Finance
- Production & Kitchen
- HR & Payroll
- POS System
- Inventory Management
- Bakery Module
- Catering
- Hire Orders
- Communication Hub
- Employee University
- Business Intelligence
- Automation
- Integrations
- And all other modules!

All features work exactly as in the web version.

