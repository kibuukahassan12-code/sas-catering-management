# ================================
# ANDROID WEBVIEW APK BUILDER
# Creates Android APK with WebView loading local HTML
# ================================

Write-Host "`n=== ANDROID WEBVIEW APK BUILDER ===`n"

$Base = "C:\Users\DELL\Desktop\sas management system"
$androidPath = "$Base\android_build"

# Create Android project folder
if (-not (Test-Path $androidPath)) {
    Write-Host "Creating Android project directory..."
    New-Item -ItemType Directory -Path $androidPath -Force | Out-Null
}

# ---------------------------------
# Create root build.gradle
# ---------------------------------
Write-Host "Creating root build.gradle..."

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
"@ | Set-Content "$androidPath\build.gradle" -Encoding UTF8

# ---------------------------------
# Create settings.gradle
# ---------------------------------
@"
include ':app'
"@ | Set-Content "$androidPath\settings.gradle" -Encoding UTF8

# ---------------------------------
# Create gradle.properties
# ---------------------------------
@"
org.gradle.jvmargs=-Xmx2048m -Dfile.encoding=UTF-8
android.useAndroidX=true
android.enableJetifier=true
"@ | Set-Content "$androidPath\gradle.properties" -Encoding UTF8

# ---------------------------------
# Create app module structure
# ---------------------------------
$appPath = "$androidPath\app"
$srcMainPath = "$appPath\src\main"
$javaPath = "$srcMainPath\java\com\sas\bestfoods"
$resPath = "$srcMainPath\res"
$layoutPath = "$resPath\layout"
$valuesPath = "$resPath\values"
$assetsPath = "$srcMainPath\assets"

New-Item -ItemType Directory -Path $javaPath -Force | Out-Null
New-Item -ItemType Directory -Path $layoutPath -Force | Out-Null
New-Item -ItemType Directory -Path $valuesPath -Force | Out-Null
New-Item -ItemType Directory -Path $assetsPath -Force | Out-Null

# ---------------------------------
# Create app-level build.gradle
# ---------------------------------
Write-Host "Creating app build.gradle..."

@"
// SAS Mobile WebView Launcher
apply plugin: 'com.android.application'

android {
    compileSdkVersion 34
    defaultConfig {
        applicationId "com.sas.bestfoods"
        minSdkVersion 24
        targetSdkVersion 34
        versionCode 1
        versionName "1.0"
    }
    buildTypes {
        release {
            minifyEnabled false
            proguardFiles getDefaultProguardFile('proguard-android-optimize.txt'), 'proguard-rules.pro'
        }
    }
}

dependencies {
    implementation 'androidx.appcompat:appcompat:1.6.1'
    implementation 'androidx.webkit:webkit:1.8.0'
}
"@ | Set-Content "$appPath\build.gradle" -Encoding UTF8

# ---------------------------------
# Create AndroidManifest.xml
# ---------------------------------
Write-Host "Creating AndroidManifest.xml..."

@"
<?xml version="1.0" encoding="utf-8"?>
<manifest xmlns:android="http://schemas.android.com/apk/res/android"
    package="com.sas.bestfoods">

    <uses-permission android:name="android.permission.INTERNET" />

    <application
        android:allowBackup="true"
        android:icon="@mipmap/ic_launcher"
        android:label="@string/app_name"
        android:theme="@style/Theme.AppCompat.Light.NoActionBar">
        <activity
            android:name=".MainActivity"
            android:exported="true"
            android:configChanges="orientation|screenSize|keyboardHidden">
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
package com.sas.bestfoods;

import android.os.Bundle;
import android.webkit.WebView;
import androidx.appcompat.app.AppCompatActivity;

public class MainActivity extends AppCompatActivity {
    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        WebView w = new WebView(this);
        setContentView(w);
        w.getSettings().setJavaScriptEnabled(true);
        w.loadUrl("file:///android_asset/index.html");
    }
}
"@ | Set-Content "$javaPath\MainActivity.java" -Encoding UTF8

# ---------------------------------
# Create layout file
# ---------------------------------
Write-Host "Creating activity_main.xml..."

@"
<?xml version="1.0" encoding="utf-8"?>
<LinearLayout xmlns:android="http://schemas.android.com/apk/res/android"
    android:layout_width="match_parent"
    android:layout_height="match_parent"
    android:orientation="vertical">

    <WebView
        android:id="@+id/sas_web"
        android:layout_width="match_parent"
        android:layout_height="match_parent" />

</LinearLayout>
"@ | Set-Content "$layoutPath\activity_main.xml" -Encoding UTF8

# ---------------------------------
# Create string resources
# ---------------------------------
Write-Host "Creating string resources..."

@"
<?xml version="1.0" encoding="utf-8"?>
<resources>
    <string name="app_name">SAS Best Foods</string>
</resources>
"@ | Set-Content "$valuesPath\strings.xml" -Encoding UTF8

# ---------------------------------
# Copy templates and static to assets
# ---------------------------------
Write-Host "`nCopying templates and static files to assets..."

$templatesSource = "$Base\sas_management\templates"
$staticSource = "$Base\sas_management\static"

if (Test-Path $templatesSource) {
    Write-Host "Copying templates from: $templatesSource"
    Copy-Item -Recurse -Path $templatesSource -Destination "$assetsPath\templates" -Force
    Write-Host "✓ Templates copied"
} else {
    Write-Host "WARNING: Templates folder not found at: $templatesSource"
}

if (Test-Path $staticSource) {
    Write-Host "Copying static files from: $staticSource"
    Copy-Item -Recurse -Path $staticSource -Destination "$assetsPath\static" -Force
    Write-Host "✓ Static files copied"
} else {
    Write-Host "WARNING: Static folder not found at: $staticSource"
}

# Check if index.html exists, if not create a basic one
$indexHtml = "$assetsPath\index.html"
if (-not (Test-Path $indexHtml)) {
    Write-Host "Creating default index.html..."
    @"
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>SAS Best Foods</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            margin: 0;
            padding: 20px;
            background: #f5f5f5;
        }
        .container {
            max-width: 800px;
            margin: 0 auto;
            background: white;
            padding: 20px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        h1 {
            color: #333;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>SAS Best Foods Management System</h1>
        <p>Welcome to the mobile app. Please ensure your templates and static files are properly configured.</p>
    </div>
</body>
</html>
"@ | Set-Content $indexHtml -Encoding UTF8
    Write-Host "✓ Default index.html created"
}

# ---------------------------------
# Create minimal launcher icon
# ---------------------------------
Write-Host "Creating launcher icon..."

$mipmapDirs = @("mipmap-mdpi", "mipmap-hdpi", "mipmap-xhdpi", "mipmap-xxhdpi", "mipmap-xxxhdpi")
foreach ($dir in $mipmapDirs) {
    $mipmapDirPath = "$resPath\$dir"
    New-Item -ItemType Directory -Path $mipmapDirPath -Force | Out-Null
}

$drawablePath = "$resPath\drawable"
New-Item -ItemType Directory -Path $drawablePath -Force | Out-Null

$mipmapAnyDpiPath = "$resPath\mipmap-anydpi-v26"
New-Item -ItemType Directory -Path $mipmapAnyDpiPath -Force | Out-Null

@"
<?xml version="1.0" encoding="utf-8"?>
<adaptive-icon xmlns:android="http://schemas.android.com/apk/res/android">
    <background android:drawable="@color/ic_launcher_background"/>
    <foreground android:drawable="@drawable/ic_launcher_foreground"/>
</adaptive-icon>
"@ | Set-Content "$mipmapAnyDpiPath\ic_launcher.xml" -Encoding UTF8

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

$gradle = Get-Command gradle -ErrorAction SilentlyContinue

if ($gradle) {
    Push-Location $androidPath
    Write-Host "Generating Gradle wrapper..."
    & gradle wrapper --gradle-version 8.1 --distribution-type all 2>&1 | Out-Null
    Pop-Location
} else {
    Write-Host "Gradle not found. Creating wrapper files manually..."
    
    $wrapperPath = "$androidPath\gradle\wrapper"
    New-Item -ItemType Directory -Path $wrapperPath -Force | Out-Null
    
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
# BUILD APK
# ---------------------------------
Write-Host "`n=== Building APK ==="
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

Write-Host "`n============================================="
Write-Host "BUILD COMPLETE!"
Write-Host "APK Location:"
Write-Host "$androidPath\app\build\outputs\apk\debug\app-debug.apk"
Write-Host "============================================="

