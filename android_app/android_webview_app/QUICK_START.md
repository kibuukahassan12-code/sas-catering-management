# Quick Start - Build SAS APK

## Step 1: Generate Icons

```powershell
python generate_icons.py
```

## Step 2: Configure Server URL (Optional)

Edit `app/src/main/res/values/strings.xml`:

```xml
<string name="server_url">http://127.0.0.1:5000</string>
```

Change to your server URL if different.

## Step 3: Build APK

```powershell
.\build_sas_apk.ps1
```

## Step 4: Install

The APK will be at: `app\build\outputs\apk\debug\app-debug.apk`

Transfer to your Android device and install!

## That's It! 🎉

Your SAS Management System is now packaged as an Android app with:
- ✅ SAS logo as icon
- ✅ All modules and features
- ✅ Full SAS branding
- ✅ Native Android experience

