# App Icon Setup Instructions

## Quick Setup (Using Android Studio)

1. **Open Android Studio**
2. **Right-click on `app` folder** → New → Image Asset
3. **Select "Launcher Icons (Adaptive and Legacy)"**
4. **Foreground Layer:**
   - Choose "Image" tab
   - Click "..." and select your SAS logo image
   - Resize if needed
   - Set padding to 20%
5. **Background Layer:**
   - Choose "Color" tab
   - Set color to `#F26822` (SAS Brand Orange)
6. **Click Next → Finish**

## Manual Setup (If you have logo files)

### Option 1: Use Existing Logo
If you have `sas_logo.png` or `ssas_logo.png`:

1. Copy the logo to `app/src/main/res/mipmap-mdpi/ic_launcher.png` (48x48)
2. Create larger versions:
   - `mipmap-hdpi/ic_launcher.png` (72x72)
   - `mipmap-xhdpi/ic_launcher.png` (96x96)
   - `mipmap-xxhdpi/ic_launcher.png` (144x144)
   - `mipmap-xxxhdpi/ic_launcher.png` (192x192)

### Option 2: Generate Icons Online
1. Go to https://icon.kitchen/ or https://www.appicon.co/
2. Upload your SAS logo
3. Download the generated icon set
4. Extract to `app/src/main/res/mipmap-*/` folders

### Option 3: Use Current Vector Icon
The app currently uses a simple vector icon. To replace:

1. Edit `app/src/main/res/drawable/ic_launcher_foreground.xml`
2. Replace the path data with your logo's SVG path
3. Or convert your PNG logo to vector format

## Current Icon Configuration

The app is configured to use:
- **Background**: SAS Brand Orange (#F26822)
- **Foreground**: White vector icon (can be replaced with your logo)

The adaptive icon XML files are already set up in:
- `app/src/main/res/mipmap-anydpi-v26/ic_launcher.xml`
- `app/src/main/res/mipmap-anydpi-v26/ic_launcher_round.xml`

## Testing the Icon

After setting up the icon:
1. Build the app: `./gradlew assembleDebug`
2. Install on device: `adb install app/build/outputs/apk/debug/app-debug.apk`
3. Check the app icon on the home screen

## Recommended Icon Sizes

- **mdpi**: 48x48 px
- **hdpi**: 72x72 px
- **xhdpi**: 96x96 px
- **xxhdpi**: 144x144 px
- **xxxhdpi**: 192x192 px

For adaptive icons (Android 8.0+):
- **Foreground**: 108x108 dp (safe zone: 72x72 dp)
- **Background**: 108x108 dp

