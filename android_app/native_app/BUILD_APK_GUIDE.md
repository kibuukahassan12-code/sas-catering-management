# Build APK Guide - SAS Management Android App

## Prerequisites

1. **Android Studio** installed (Hedgehog or later)
2. **JDK 17** or later
3. **Android SDK** with API 34
4. **Flask Backend** running (for testing login)

## Step 1: Configure Backend URL

Before building, configure your backend URL in:
`app/src/main/java/com/sas/management/data/api/ApiClient.kt`

```kotlin
// For Android Emulator
private const val BASE_URL = "http://10.0.2.2:10000"

// For Physical Device (replace with your computer's IP)
private const val BASE_URL = "http://192.168.1.XXX:10000"

// For Production
private const val BASE_URL = "https://your-domain.com"
```

## Step 2: Build APK

### Option A: Using Android Studio (Recommended)

1. Open the project in Android Studio
2. Wait for Gradle sync to complete
3. Go to **Build** → **Build Bundle(s) / APK(s)** → **Build APK(s)**
4. Wait for build to complete
5. Click **locate** in the notification to find the APK
6. APK will be at: `app/build/outputs/apk/debug/app-debug.apk`

### Option B: Using Command Line (Windows)

```powershell
cd android_app\native_app
.\build_apk.ps1
```

### Option C: Using Command Line (Mac/Linux)

```bash
cd android_app/native_app
chmod +x build_apk.sh
./build_apk.sh
```

### Option D: Using Gradle Directly

```bash
cd android_app/native_app
./gradlew assembleDebug
```

The APK will be generated at:
`app/build/outputs/apk/debug/app-debug.apk`

## Step 3: Install APK

### On Physical Device

1. Enable **Developer Options** on your Android device:
   - Go to Settings → About Phone
   - Tap "Build Number" 7 times
2. Enable **USB Debugging**:
   - Settings → Developer Options → USB Debugging
3. Connect device via USB
4. Install APK:
   ```bash
   adb install app/build/outputs/apk/debug/app-debug.apk
   ```

### On Emulator

1. Start Android Emulator
2. Drag and drop the APK file onto the emulator
3. Or use: `adb install app/build/outputs/apk/debug/app-debug.apk`

## Step 4: Test the App

1. **Start Flask Backend:**
   ```bash
   python -m sas_management.app
   ```

2. **Open the app** on your device/emulator

3. **Test Login:**
   - Enter your email and password
   - Should navigate to dashboard on success

4. **Test Modules:**
   - Click "View All Modules" button on dashboard
   - Should see all 40+ modules
   - Click any module to see details

## Troubleshooting

### Build Errors

**Error: "Gradle sync failed"**
- Open Android Studio
- File → Invalidate Caches → Restart
- File → Sync Project with Gradle Files

**Error: "SDK not found"**
- Open Android Studio
- Tools → SDK Manager
- Install Android SDK Platform 34
- Install Android SDK Build-Tools

**Error: "JDK not found"**
- File → Project Structure → SDK Location
- Set JDK location to JDK 17

### Runtime Errors

**"Cannot connect to server"**
- Check backend URL in `ApiClient.kt`
- Ensure Flask backend is running
- For physical device: Use computer's IP, not localhost
- Check firewall settings

**"Login failed"**
- Verify backend is accessible
- Check email/password are correct
- Check backend logs for errors

## APK Size

Expected APK size: **15-25 MB** (debug build)

To reduce size:
- Use ProGuard for release builds
- Enable code shrinking
- Remove unused resources

## Release APK

For production release:

1. **Generate signing key:**
   ```bash
   keytool -genkey -v -keystore sas-release-key.jks -keyalg RSA -keysize 2048 -validity 10000 -alias sas
   ```

2. **Configure signing in `app/build.gradle`:**
   ```gradle
   android {
       signingConfigs {
           release {
               storeFile file('sas-release-key.jks')
               storePassword 'your-password'
               keyAlias 'sas'
               keyPassword 'your-password'
           }
       }
       buildTypes {
           release {
               signingConfig signingConfigs.release
               minifyEnabled true
               proguardFiles getDefaultProguardFile('proguard-android-optimize.txt'), 'proguard-rules.pro'
           }
       }
   }
   ```

3. **Build release APK:**
   ```bash
   ./gradlew assembleRelease
   ```

4. **APK location:**
   `app/build/outputs/apk/release/app-release.apk`

## Features in APK

✅ **Login Screen** - Matches web UI
✅ **Dashboard** - KPI cards and summary
✅ **All Modules** - 40+ modules accessible
✅ **Navigation** - Bottom nav and drawer
✅ **SAS Branding** - Orange theme and colors
✅ **API Integration** - Connects to Flask backend

## Next Steps

After successful build:
1. Test all features
2. Add more module screens as needed
3. Optimize for production
4. Generate signed release APK
5. Distribute to users

