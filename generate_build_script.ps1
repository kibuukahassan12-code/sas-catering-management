# Delete old script
if (Test-Path "create_and_build.ps1") { Remove-Item create_and_build.ps1 -Force }

Add-Content create_and_build.ps1 'Write-Host "Starting Android build..."'

Add-Content create_and_build.ps1 'if (Test-Path android_build) { Remove-Item android_build -Recurse -Force }'

Add-Content create_and_build.ps1 'New-Item -Type Directory android_build | Out-Null'

Add-Content create_and_build.ps1 'Set-Location android_build'

Add-Content create_and_build.ps1 'New-Item -Type Directory app/src/main/java/com/sas/management -Force | Out-Null'

Add-Content create_and_build.ps1 'New-Item -Type Directory app/src/main/assets/www -Force | Out-Null'

Add-Content create_and_build.ps1 'New-Item -Type Directory app/src/main/python -Force | Out-Null'

Add-Content create_and_build.ps1 'echo rootProject.name=SASApp > settings.gradle'

Add-Content create_and_build.ps1 'echo include :app >> settings.gradle'

Add-Content create_and_build.ps1 'echo buildscript { repositories { google(); mavenCentral() } dependencies { classpath \"com.android.tools.build:gradle:8.0.2\"; classpath \"com.chaquo.python:gradle:15.0.1\" } } > build.gradle'

Add-Content create_and_build.ps1 'echo allprojects { repositories { google(); mavenCentral() } } >> build.gradle'

Add-Content create_and_build.ps1 'echo android.useAndroidX=true > gradle.properties'

Add-Content create_and_build.ps1 'echo android.enableJetifier=true >> gradle.properties'

Add-Content create_and_build.ps1 'echo plugins { id \"com.android.application\"; id \"com.chaquo.python\" } > app/build.gradle'

Add-Content create_and_build.ps1 'echo android { namespace \"com.sas.management\"; compileSdk 33; defaultConfig { applicationId \"com.sas.management\"; minSdk 21; targetSdk 33; versionCode 1; versionName \"1.0\" } sourceSets { main { python.srcDirs = [\"src/main/python\"]; assets.srcDirs = [\"src/main/assets\"] } } } >> app/build.gradle'

Add-Content create_and_build.ps1 'echo chaquopy { python { pip { install = [] } } } >> app/build.gradle'

Add-Content create_and_build.ps1 'echo dependencies { implementation \"androidx.appcompat:appcompat:1.6.1\" } >> app/build.gradle'

# AndroidManifest.xml
Add-Content create_and_build.ps1 '@\"'
Add-Content create_and_build.ps1 '<?xml version=\"1.0\" encoding=\"utf-8\"?>'
Add-Content create_and_build.ps1 '<manifest package=\"com.sas.management\" xmlns:android=\"http://schemas.android.com/apk/res/android\">'
Add-Content create_and_build.ps1 '<uses-permission android:name=\"android.permission.INTERNET\"/>'
Add-Content create_and_build.ps1 '<application android:label=\"SAS Management\" android:usesCleartextTraffic=\"true\">'
Add-Content create_and_build.ps1 '<activity android:name=\".MainActivity\" android:exported=\"true\">'
Add-Content create_and_build.ps1 '<intent-filter>'
Add-Content create_and_build.ps1 '<action android:name=\"android.intent.action.MAIN\"/>'
Add-Content create_and_build.ps1 '<category android:name=\"android.intent.category.LAUNCHER\"/>'
Add-Content create_and_build.ps1 '</intent-filter>'
Add-Content create_and_build.ps1 '</activity>'
Add-Content create_and_build.ps1 '</application>'
Add-Content create_and_build.ps1 '</manifest>'
Add-Content create_and_build.ps1 '\"@ | Out-File app/src/main/AndroidManifest.xml -Encoding UTF8'

# MainActivity.java
Add-Content create_and_build.ps1 '@\"'
Add-Content create_and_build.ps1 'package com.sas.management;'
Add-Content create_and_build.ps1 'import androidx.appcompat.app.AppCompatActivity;'
Add-Content create_and_build.ps1 'import android.os.Bundle;'
Add-Content create_and_build.ps1 'import android.webkit.WebView;'
Add-Content create_and_build.ps1 'import android.webkit.WebViewClient;'
Add-Content create_and_build.ps1 'import com.chaquo.python.Python;'
Add-Content create_and_build.ps1 'import com.chaquo.python.android.AndroidPlatform;'
Add-Content create_and_build.ps1 'public class MainActivity extends AppCompatActivity {'
Add-Content create_and_build.ps1 '@Override'
Add-Content create_and_build.ps1 'protected void onCreate(Bundle savedInstanceState) {'
Add-Content create_and_build.ps1 'super.onCreate(savedInstanceState);'
Add-Content create_and_build.ps1 'if (!Python.isStarted()) { Python.start(new AndroidPlatform(this)); }'
Add-Content create_and_build.ps1 'WebView w = new WebView(this);'
Add-Content create_and_build.ps1 'w.getSettings().setJavaScriptEnabled(true);'
Add-Content create_and_build.ps1 'w.setWebViewClient(new WebViewClient());'
Add-Content create_and_build.ps1 'setContentView(w);'
Add-Content create_and_build.ps1 'w.loadUrl(\"file:///android_asset/www/index.html\");'
Add-Content create_and_build.ps1 '}'
Add-Content create_and_build.ps1 '}'
Add-Content create_and_build.ps1 '\"@ | Out-File app/src/main/java/com/sas/management/MainActivity.java -Encoding UTF8'

Add-Content create_and_build.ps1 'echo <!DOCTYPE html><html><head><title>SAS Mobile</title></head><body><h1>SAS Mobile</h1><p>Offline version running.</p></body></html> > app/src/main/assets/www/index.html'

Add-Content create_and_build.ps1 'echo print(\"Python backend running\") > app/src/main/python/backend.py'

Add-Content create_and_build.ps1 'echo Building APK...'

Add-Content create_and_build.ps1 'if (Get-Command gradle -ErrorAction SilentlyContinue) { gradle wrapper } else { echo gradle %* > gradlew.bat }'

Add-Content create_and_build.ps1 'if (Test-Path gradlew.bat) { ./gradlew.bat assembleDebug } else { Write-Host "Gradle wrapper missing" }'

Add-Content create_and_build.ps1 'Write-Host "APK finished at android_build/app/build/outputs/apk/debug"'

Add-Content create_and_build.ps1 'Set-Location ..'

Write-Host "NEW script created successfully."
