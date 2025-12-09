# ================================
# ANDROID APK AUTO-BUILDER SCRIPT
# CLEAN VERSION (NO ENCODING ERRORS)
# ================================

Write-Host "`n=== ANDROID APK AUTO BUILDER ===`n"

# ---------------------------------
# Validate Android SDK
# ---------------------------------
if (-not $env:ANDROID_SDK_ROOT -and -not $env:ANDROID_HOME) {
    Write-Host "ERROR: ANDROID_SDK_ROOT not set!"
    Write-Host "Please install Android SDK and set:"
    Write-Host 'setx ANDROID_SDK_ROOT "C:\Users\DELL\AppData\Local\Android\Sdk"'
    exit 1
}

if ($env:ANDROID_SDK_ROOT) {
    $sdk = $env:ANDROID_SDK_ROOT
} else {
    $sdk = $env:ANDROID_HOME
}

Write-Host "Using Android SDK: $sdk"

# ---------------------------------
# Validate Java
# ---------------------------------
$java = Get-Command java -ErrorAction SilentlyContinue

if (-not $java) {
    Write-Host "ERROR: Java JDK not installed!"
    Write-Host "Download JDK here: https://adoptium.net"
    exit 1
}
else {
    Write-Host "Java detected: $($java.Source)"
}

# ---------------------------------
# Validate Gradle
# ---------------------------------
$gradle = Get-Command gradle -ErrorAction SilentlyContinue

if ($gradle) {
    Write-Host "Gradle detected: $($gradle.Source)"
} else {
    Write-Host "Gradle not found — using Gradle Wrapper instead."
}

# ---------------------------------
# Create Android project folder
# ---------------------------------
$androidPath = "android_build"

if (-not (Test-Path $androidPath)) {
    Write-Host "Creating Android project directory..."
    New-Item -ItemType Directory -Path $androidPath | Out-Null
}

# ---------------------------------
# Create minimal Gradle project
# ---------------------------------
Write-Host "Writing Gradle project files..."

# Root-level build.gradle
@"
buildscript {
    repositories {
        google()
        mavenCentral()
    }
    dependencies {
        classpath 'com.android.tools.build:gradle:8.1.0'
    }
}

allprojects {
    repositories {
        google()
        mavenCentral()
    }
}

task clean(type: Delete) {
    delete rootProject.buildDir
}
"@ | Set-Content "$androidPath\build.gradle"

@"
include ':app'
"@ | Set-Content "$androidPath\settings.gradle"

# Gradle properties
@"
org.gradle.jvmargs=-Xmx2048m -Dfile.encoding=UTF-8
android.useAndroidX=true
android.enableJetifier=true
"@ | Set-Content "$androidPath\gradle.properties"

# ---------------------------------
# Create app module
# ---------------------------------
$appPath = "$androidPath\app"

if (-not (Test-Path $appPath)) {
    New-Item -ItemType Directory -Path $appPath | Out-Null
}

# App-level Gradle file
@"
plugins {
    id 'com.android.application'
}

android {
    namespace "com.sas.management"
    compileSdk 34

    defaultConfig {
        applicationId "com.sas.management"
        minSdk 23
        targetSdk 34
        versionCode 1
        versionName "1.0"
    }

    buildTypes {
        release {
            minifyEnabled false
        }
    }
}

dependencies {
    implementation 'androidx.appcompat:appcompat:1.6.1'
}
"@ | Set-Content "$appPath\build.gradle"

# ---------------------------------
# Create source directories
# ---------------------------------
$srcMainPath = "$appPath\src\main"
$javaPath = "$srcMainPath\java\com\sas\management"
$resPath = "$srcMainPath\res"
$valuesPath = "$resPath\values"

New-Item -ItemType Directory -Path $javaPath -Force | Out-Null
New-Item -ItemType Directory -Path $valuesPath -Force | Out-Null

# ---------------------------------
# Create AndroidManifest.xml
# ---------------------------------
Write-Host "Creating AndroidManifest.xml..."

@"
<?xml version="1.0" encoding="utf-8"?>
<manifest xmlns:android="http://schemas.android.com/apk/res/android"
    package="com.sas.management">

    <uses-permission android:name="android.permission.INTERNET" />

    <application
        android:allowBackup="true"
        android:icon="@mipmap/ic_launcher"
        android:label="@string/app_name"
        android:theme="@android:style/Theme.Material.Light">
        <activity
            android:name=".MainActivity"
            android:exported="true">
            <intent-filter>
                <action android:name="android.intent.action.MAIN" />
                <category android:name="android.intent.category.LAUNCHER" />
            </intent-filter>
        </activity>
    </application>

</manifest>
"@ | Set-Content "$srcMainPath\AndroidManifest.xml" -Encoding UTF8

# ---------------------------------
# Create MainActivity.java
# ---------------------------------
Write-Host "Creating MainActivity.java..."

@"
package com.sas.management;

import android.os.Bundle;
import androidx.appcompat.app.AppCompatActivity;

public class MainActivity extends AppCompatActivity {
    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_main);
    }
}
"@ | Set-Content "$javaPath\MainActivity.java" -Encoding UTF8

# ---------------------------------
# Create layout file
# ---------------------------------
$layoutPath = "$resPath\layout"
New-Item -ItemType Directory -Path $layoutPath -Force | Out-Null

@"
<?xml version="1.0" encoding="utf-8"?>
<LinearLayout xmlns:android="http://schemas.android.com/apk/res/android"
    android:layout_width="match_parent"
    android:layout_height="match_parent"
    android:orientation="vertical"
    android:gravity="center"
    android:padding="16dp">

    <TextView
        android:layout_width="wrap_content"
        android:layout_height="wrap_content"
        android:text="@string/app_name"
        android:textSize="24sp"
        android:textStyle="bold" />

    <TextView
        android:layout_width="wrap_content"
        android:layout_height="wrap_content"
        android:text="@string/welcome_message"
        android:textSize="16sp"
        android:layout_marginTop="16dp" />

</LinearLayout>
"@ | Set-Content "$layoutPath\activity_main.xml" -Encoding UTF8

# ---------------------------------
# Create string resources
# ---------------------------------
Write-Host "Creating string resources..."

@"
<?xml version="1.0" encoding="utf-8"?>
<resources>
    <string name="app_name">SAS Management</string>
    <string name="welcome_message">Welcome to SAS Management System</string>
</resources>
"@ | Set-Content "$valuesPath\strings.xml" -Encoding UTF8

# ---------------------------------
# Create minimal launcher icon
# ---------------------------------
Write-Host "Creating launcher icon..."

# Create mipmap directories for different densities
$mipmapDirs = @("mipmap-mdpi", "mipmap-hdpi", "mipmap-xhdpi", "mipmap-xxhdpi", "mipmap-xxxhdpi")
foreach ($dir in $mipmapDirs) {
    $mipmapDirPath = "$resPath\$dir"
    New-Item -ItemType Directory -Path $mipmapDirPath -Force | Out-Null
    
    # Create adaptive icon XML
    @"
<?xml version="1.0" encoding="utf-8"?>
<adaptive-icon xmlns:android="http://schemas.android.com/apk/res/android">
    <background android:drawable="@color/ic_launcher_background"/>
    <foreground android:drawable="@drawable/ic_launcher_foreground"/>
</adaptive-icon>
"@ | Set-Content "$mipmapDirPath\ic_launcher.xml" -Encoding UTF8
}

# Create drawable for foreground icon
$drawablePath = "$resPath\drawable"
New-Item -ItemType Directory -Path $drawablePath -Force | Out-Null

@"
<?xml version="1.0" encoding="utf-8"?>
<vector xmlns:android="http://schemas.android.com/apk/res/android"
    android:width="108dp"
    android:height="108dp"
    android:viewportWidth="108"
    android:viewportHeight="108">
    <path
        android:fillColor="#FFFFFF"
        android:pathData="M54,20c-8.28,0 -15,6.72 -15,15s6.72,15 15,15 15,-6.72 15,-15 -6.72,-15 -15,-15zM54,60c-6.63,0 -12,5.37 -12,12h24c0,-6.63 -5.37,-12 -12,-12z"/>
</vector>
"@ | Set-Content "$drawablePath\ic_launcher_foreground.xml" -Encoding UTF8

# Create colors
@"
<?xml version="1.0" encoding="utf-8"?>
<resources>
    <color name="ic_launcher_background">#3F51B5</color>
</resources>
"@ | Set-Content "$valuesPath\colors.xml" -Encoding UTF8

# ---------------------------------
# Create Gradle Wrapper
# ---------------------------------
Write-Host "`nSetting up Gradle Wrapper..."

if ($gradle) {
    Push-Location $androidPath
    Write-Host "Generating Gradle wrapper..."
    & gradle wrapper --gradle-version 8.1 --distribution-type all 2>&1 | Out-Null
    Pop-Location
} else {
    Write-Host "Gradle not found. Creating wrapper files manually..."
    
    $wrapperPath = "$androidPath\gradle\wrapper"
    New-Item -ItemType Directory -Path $wrapperPath -Force | Out-Null
    
    # Create gradle-wrapper.properties
    @"
distributionBase=GRADLE_USER_HOME
distributionPath=wrapper/dists
distributionUrl=https\://services.gradle.org/distributions/gradle-8.1-bin.zip
networkTimeout=10000
zipStoreBase=GRADLE_USER_HOME
zipStorePath=wrapper/dists
"@ | Set-Content "$wrapperPath\gradle-wrapper.properties" -Encoding UTF8
    
    Write-Host "WARNING: Gradle wrapper JAR not included. You may need to run 'gradle wrapper' manually."
}

# ---------------------------------
# Warn if platform-tools missing
# ---------------------------------
if (-not (Test-Path "$sdk\platform-tools")) {
    Write-Host "`nWARNING: Android Platform Tools not installed!"
    Write-Host "Install using Android Studio OR run:"
    Write-Host "`$sdk\cmdline-tools\latest\bin\sdkmanager.bat ""platform-tools"" ""build-tools;34.0.0""" 
}

# ---------------------------------
# BUILD APK
# ---------------------------------
Write-Host "`nBuilding APK..."
Push-Location $androidPath

if (Test-Path ".\gradlew.bat") {
    Write-Host "Using Gradle Wrapper..."
    & .\gradlew.bat assembleDebug
} elseif ($gradle) {
    Write-Host "Using system Gradle..."
    & gradle assembleDebug
} else {
    Write-Host "ERROR: No Gradle found. Please install Gradle or run 'gradle wrapper' in $androidPath"
    Pop-Location
    exit 1
}

Pop-Location

Write-Host "`nBuild complete!"
Write-Host "APK Location:"
Write-Host "android_build/app/build/outputs/apk/debug/app-debug.apk"
