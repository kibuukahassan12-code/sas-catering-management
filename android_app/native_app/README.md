# SAS Management System - Native Android App

A native Android application built with Kotlin and Jetpack Compose, matching the web UI of the SAS Management System.

## ✅ Status: Ready for APK Generation

All features are implemented and the app is ready to build!

## Quick Start

1. **Open in Android Studio**
   - File → Open → Select this folder
   - Wait for Gradle sync

2. **Configure Backend URL**
   - Edit `app/src/main/java/com/sas/management/data/api/ApiClient.kt`
   - Set `BASE_URL` to your Flask backend

3. **Build APK**
   - Build → Build Bundle(s) / APK(s) → Build APK(s)
   - Or run: `.\build_apk.ps1` (Windows) or `./build_apk.sh` (Mac/Linux)

4. **Install & Test**
   - Install APK on device: `adb install app/build/outputs/apk/debug/app-debug.apk`
   - Start Flask backend: `python -m sas_management.app`
   - Test login with your credentials

## Features

✅ **Login** - Matches web UI, connects to Flask backend
✅ **Dashboard** - KPI cards and summary
✅ **All Modules** - 40+ modules accessible
✅ **Navigation** - Bottom nav and drawer
✅ **SAS Branding** - Orange theme (#F26822)
✅ **App Icon** - SAS brand colors

## Documentation

- **BUILD_APK_GUIDE.md** - Detailed build instructions
- **QUICK_START.md** - 5-minute setup guide
- **ICON_SETUP.md** - How to add custom logo
- **APK_GENERATION_COMPLETE.md** - Complete feature list

## Tech Stack

- Kotlin
- Jetpack Compose
- Material Design 3
- Retrofit (Networking)
- MVVM Architecture

## Requirements

- Android Studio Hedgehog (2023.1.1) or later
- JDK 17+
- Android SDK API 34
- Min SDK: 24 (Android 7.0)

## Project Structure

```
app/src/main/java/com/sas/management/
├── MainActivity.kt          # Entry point
├── data/                   # API and models
├── ui/                     # Screens and UI
├── viewmodel/              # ViewModels
└── navigation/            # Navigation setup
```

## Build Commands

**Debug APK:**
```bash
./gradlew assembleDebug
```

**Release APK:**
```bash
./gradlew assembleRelease
```

**Clean Build:**
```bash
./gradlew clean assembleDebug
```

## APK Location

After building, find APK at:
`app/build/outputs/apk/debug/app-debug.apk`

## Support

See BUILD_APK_GUIDE.md for troubleshooting and detailed instructions.
