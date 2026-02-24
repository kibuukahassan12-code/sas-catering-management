# SAS Management System - Android APK

This directory contains the Android WebView application that packages the SAS Management System as a native Android APK.

## Features

✅ **Full SAS Branding**
- SAS logo as app icon (all densities)
- SAS Best Foods branding throughout
- Consistent UI/UX with web version

✅ **All Modules Included**
- Dashboard
- Event Service Department
- Accounting
- Production
- HR & Payroll
- POS System
- Inventory
- Bakery
- Catering
- Hire Orders
- Communication Hub
- Employee University
- Business Intelligence
- Automation
- Integrations
- And all other SAS modules

✅ **Native Android Experience**
- WebView-based interface
- Offline error handling
- Progress indicators
- Back button support
- Hardware acceleration

## Prerequisites

1. **Android SDK** - Android SDK Platform 34 or higher
2. **Java JDK** - JDK 17 or higher
3. **Gradle** - Included via Gradle Wrapper
4. **Python** - For icon generation (PIL/Pillow required)

## Quick Start

### 1. Generate Icons

First, generate the app icons from the SAS logo:

```powershell
python generate_icons.py
```

This creates icons in all required densities (mdpi, hdpi, xhdpi, xxhdpi, xxxhdpi).

### 2. Configure Server URL

Edit `app/src/main/res/values/strings.xml` and update the server URL:

```xml
<string name="server_url">http://127.0.0.1:5000</string>
```

For production, change to your production server:
```xml
<string name="server_url">https://your-production-server.com</string>
```

### 3. Build Debug APK

Run the build script:

```powershell
.\build_sas_apk.ps1
```

The APK will be generated at:
```
app/build/outputs/apk/debug/app-debug.apk
```

### 4. Build Release APK (for distribution)

For a signed release APK:

```powershell
.\build_release_apk.ps1
```

**Note:** You'll need to set up signing configuration in `app/build.gradle` for release builds.

## Manual Build

If you prefer to build manually:

```powershell
# Clean
.\gradlew.bat clean

# Build debug
.\gradlew.bat assembleDebug

# Build release (requires signing config)
.\gradlew.bat assembleRelease
```

## Installation

1. **Enable Unknown Sources**
   - Go to Android Settings → Security
   - Enable "Install from Unknown Sources" or "Install Unknown Apps"

2. **Transfer APK to Device**
   - Use USB, email, or cloud storage
   - Or use ADB: `adb install app-debug.apk`

3. **Install**
   - Open the APK file on your device
   - Follow the installation prompts

## Configuration

### Server URL

The app connects to the Flask server specified in `strings.xml`. 

**For Development:**
- Use `http://127.0.0.1:5000` for localhost
- Ensure your device and computer are on the same network
- Use your computer's local IP instead of 127.0.0.1 (e.g., `http://192.168.1.100:5000`)

**For Production:**
- Use your production server URL (e.g., `https://sas.yourcompany.com`)
- Ensure HTTPS is configured for security

### App Name & Branding

Edit `app/src/main/res/values/strings.xml` to customize:
- App name
- Server URLs
- Other strings

### App Icon

Icons are generated from `sas_logo.png` in the project root. To regenerate:

```powershell
python generate_icons.py
```

## Troubleshooting

### Build Fails

1. **Check Java Version**
   ```powershell
   java -version
   ```
   Should be JDK 17 or higher.

2. **Check Android SDK**
   - Ensure Android SDK Platform 34 is installed
   - Set `ANDROID_HOME` environment variable

3. **Clean and Rebuild**
   ```powershell
   .\gradlew.bat clean
   .\gradlew.bat assembleDebug
   ```

### App Won't Connect

1. **Check Server URL**
   - Verify the URL in `strings.xml`
   - Ensure the server is running
   - Check firewall settings

2. **Network Issues**
   - For localhost, use your computer's IP address
   - Ensure device and server are on the same network
   - Check if port 5000 is accessible

3. **HTTPS/SSL**
   - For HTTPS, ensure certificates are valid
   - The app allows cleartext traffic for development

### Icons Not Showing

1. **Regenerate Icons**
   ```powershell
   python generate_icons.py
   ```

2. **Clean Build**
   ```powershell
   .\gradlew.bat clean
   .\gradlew.bat assembleDebug
   ```

## Project Structure

```
android_webview_app/
├── app/
│   ├── src/
│   │   └── main/
│   │       ├── java/com/sas/management/
│   │       │   ├── MainActivity.java      # Main WebView activity
│   │       │   └── SASApplication.java    # Application class
│   │       ├── res/
│   │       │   ├── layout/
│   │       │   │   └── activity_main.xml  # Main layout
│   │       │   ├── values/
│   │       │   │   └── strings.xml         # App strings & config
│   │       │   └── mipmap-*/              # App icons (generated)
│   │       └── AndroidManifest.xml         # App manifest
│   └── build.gradle                        # App build config
├── build.gradle                            # Project build config
├── generate_icons.py                       # Icon generator script
├── build_sas_apk.ps1                      # Debug build script
└── build_release_apk.ps1                  # Release build script
```

## Features Included

The APK includes access to all SAS Management System modules:

- ✅ Dashboard & Analytics
- ✅ Event Service Department
- ✅ Accounting & Finance
- ✅ Production & Kitchen
- ✅ HR & Payroll
- ✅ POS System
- ✅ Inventory Management
- ✅ Bakery Module
- ✅ Catering
- ✅ Hire Orders
- ✅ Communication Hub
- ✅ Employee University
- ✅ Business Intelligence
- ✅ Automation
- ✅ Integrations
- ✅ CRM & Leads
- ✅ Vendors
- ✅ Reports
- ✅ Admin Panel
- ✅ And more...

All features work exactly as in the web version, with full mobile optimization.

## Support

For issues or questions:
1. Check the main SAS Management System documentation
2. Review build logs for errors
3. Ensure all prerequisites are installed
4. Verify server connectivity

## License

Same as the main SAS Management System project.

