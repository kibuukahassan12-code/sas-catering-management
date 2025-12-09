# SAS Android WebView App

A complete Android WebView application that loads https://sasbestfoods.com/app/

## Project Structure

```
android_webview_app/
├── app/
│   ├── build.gradle              # Module build configuration
│   ├── proguard-rules.pro        # ProGuard rules
│   └── src/
│       └── main/
│           ├── AndroidManifest.xml
│           ├── java/com/sas/management/
│           │   └── MainActivity.java
│           └── res/
│               ├── layout/
│               │   └── activity_main.xml
│               └── mipmap-*/
│                   └── ic_launcher.png
├── gradle/
│   └── wrapper/
│       ├── gradle-wrapper.jar
│       └── gradle-wrapper.properties
├── build.gradle                  # Project build configuration
├── settings.gradle               # Project settings
├── gradle.properties            # Gradle properties
├── gradlew                       # Unix Gradle wrapper
├── gradlew.bat                   # Windows Gradle wrapper
└── build_apk.ps1                 # Build script

```

## Requirements

- **compileSdk**: 34
- **targetSdk**: 34
- **minSdk**: 23
- **Java**: 17

## Features

- ✅ WebView with JavaScript enabled
- ✅ File upload support
- ✅ Hardware acceleration
- ✅ Back button navigation
- ✅ Custom SAS logo as launcher icon

## Building the APK

### Windows (PowerShell)

```powershell
cd android_webview_app
powershell -ExecutionPolicy Bypass -File build_apk.ps1
```

The script will:
1. Copy the SAS logo to all mipmap folders
2. Clean the project
3. Build the debug APK
4. Open the output folder on success

### Manual Build

```bash
# Windows
gradlew.bat clean assembleDebug

# Linux/Mac
./gradlew clean assembleDebug
```

## Output

The APK will be located at:
```
app/build/outputs/apk/debug/app-debug.apk
```

## Notes

- The app loads: https://sasbestfoods.com/app/
- Logo source: `../../sas_logo.png` (relative to project root)
- If gradle-wrapper.jar is missing, the build script will attempt to download it automatically

