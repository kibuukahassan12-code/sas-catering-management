# Quick Start Guide

## 🚀 Get Started in 5 Minutes

### Step 1: Open Project
1. Open Android Studio
2. File → Open → Select `android_app/native_app` folder
3. Wait for Gradle sync to complete

### Step 2: Configure Backend
Edit `app/src/main/java/com/sas/management/data/api/ApiClient.kt`:

**For Android Emulator:**
```kotlin
private const val BASE_URL = "http://10.0.2.2:10000"
```

**For Physical Device:**
1. Find your computer's IP address:
   - Windows: `ipconfig` → Look for IPv4 Address
   - Mac/Linux: `ifconfig` → Look for inet
2. Update the URL:
```kotlin
private const val BASE_URL = "http://192.168.1.XXX:10000" // Replace XXX
```

**For Production:**
```kotlin
private const val BASE_URL = "https://your-domain.com"
```

### Step 3: Start Flask Backend
Make sure your Flask backend is running:
```bash
python -m sas_management.app
# Or
python run_backend.py
```

The backend should be accessible at `http://localhost:10000`

### Step 4: Run Android App
1. Connect an Android device or start an emulator
2. Click the green "Run" button in Android Studio
3. Select your device/emulator
4. Wait for the app to install and launch

### Step 5: Test Login
- Use your Flask backend credentials
- Email: (your admin email)
- Password: (your password)

## ✅ What You Should See

1. **Splash Screen** - SAS logo with loading indicator
2. **Login Screen** - Email and password fields matching web UI
3. **Dashboard** - KPI cards showing:
   - Upcoming Events
   - Pipeline Value
   - Active Staff
   - Pending Tasks

## 🔧 Troubleshooting

### "Network Error" or "Connection Failed"
- ✅ Check Flask backend is running
- ✅ Verify BASE_URL is correct
- ✅ For physical device: Ensure phone and computer on same WiFi
- ✅ Check firewall isn't blocking port 10000

### "Build Failed"
- ✅ Ensure JDK 17 is installed
- ✅ File → Invalidate Caches → Restart
- ✅ Build → Clean Project → Rebuild

### "App Crashes on Launch"
- ✅ Check AndroidManifest.xml permissions
- ✅ Verify minSdk is 24 or lower
- ✅ Check Logcat for error messages

## 📱 Testing Checklist

- [ ] App launches without crashes
- [ ] Splash screen displays
- [ ] Login screen matches web UI
- [ ] Can enter email and password
- [ ] Login button works
- [ ] Dashboard loads after login
- [ ] KPI cards display data
- [ ] Bottom navigation visible
- [ ] Top app bar shows menu

## 🎯 Next Steps

Once basic functionality works:
1. Add more screens (Events, POS, etc.)
2. Implement drawer navigation
3. Add search functionality
4. Enhance UI with animations
5. Add offline support

## 📞 Need Help?

Check the main README.md for detailed documentation.

