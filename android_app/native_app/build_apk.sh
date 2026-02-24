#!/bin/bash
# Build APK Script for SAS Management Android App

echo "========================================"
echo "SAS Management - APK Build Script"
echo "========================================"
echo ""

# Check if we're in the right directory
if [ ! -f "app/build.gradle" ]; then
    echo "Error: Please run this script from the android_app/native_app directory"
    exit 1
fi

# Check if Gradle wrapper exists
if [ ! -f "gradlew" ]; then
    echo "Error: Gradle wrapper not found. Please initialize the project in Android Studio first."
    exit 1
fi

echo "Step 1: Cleaning previous builds..."
./gradlew clean
if [ $? -ne 0 ]; then
    echo "Error: Clean failed"
    exit 1
fi

echo ""
echo "Step 2: Building debug APK..."
./gradlew assembleDebug
if [ $? -ne 0 ]; then
    echo "Error: Build failed"
    exit 1
fi

echo ""
echo "Step 3: Checking APK location..."
APK_PATH="app/build/outputs/apk/debug/app-debug.apk"
if [ -f "$APK_PATH" ]; then
    APK_SIZE=$(du -h "$APK_PATH" | cut -f1)
    echo ""
    echo "========================================"
    echo "✓ APK Build Successful!"
    echo "========================================"
    echo "APK Location: $APK_PATH"
    echo "APK Size: $APK_SIZE"
    echo ""
    echo "To install on device:"
    echo "  adb install $APK_PATH"
    echo ""
    
    # Copy to root
    read -p "Copy APK to project root? (y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        cp "$APK_PATH" "../../sas-management-app.apk"
        echo "APK copied to: ../../sas-management-app.apk"
    fi
else
    echo "Error: APK not found at expected location"
    exit 1
fi

echo ""
echo "Build complete!"

