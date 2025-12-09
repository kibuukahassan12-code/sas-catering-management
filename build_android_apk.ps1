$project = 'C:/Users/DELL/Desktop/sas management system/android_app/android_webview_app';

Set-Location $project;

# Set JAVA_HOME to JDK 17 to ensure Gradle uses the correct JDK version
$env:JAVA_HOME = 'C:/Program Files/Java/jdk-17';
$env:PATH = "$env:JAVA_HOME\bin;$env:PATH";

Write-Host '=== FIX 0: Setting JAVA_HOME to JDK 17 ===';
Write-Host "JAVA_HOME: $env:JAVA_HOME";
Write-Host "Java version:";
& java -version;

Write-Host '=== FIX 1: Ensure gradlew exists ===';

if (-not(Test-Path 'gradlew.bat')) {
    Write-Host 'Creating gradlew wrapper...';
    & 'C:/Program Files/Java/jdk-17/bin/java.exe' -classpath 'gradle/wrapper/gradle-wrapper.jar' org.gradle.wrapper.GradleWrapperMain;
    if ($LASTEXITCODE -ne 0) { exit 1 }
}

Write-Host '=== FIX 2: Ensure Android icon exists ===';

$mip = Join-Path $project 'app/src/main/res';
$icon = 'sas_logo.png';
$targets = @('mipmap-mdpi','mipmap-hdpi','mipmap-xhdpi','mipmap-xxhdpi','mipmap-xxxhdpi');

foreach ($t in $targets) {
    $d = Join-Path $mip $t;
    if (-not(Test-Path $d)) { New-Item -ItemType Directory $d | Out-Null }
    Copy-Item $icon (Join-Path $d 'ic_launcher.png') -Force -ErrorAction SilentlyContinue
}

Write-Host '=== FIX 3: Clean build ===';

./gradlew.bat clean --no-daemon

Write-Host '=== BUILDING APK — PLEASE WAIT 5–10 MINUTES ===';

./gradlew.bat assembleDebug --no-daemon

$apk = Join-Path $project 'app/build/outputs/apk/debug/app-debug.apk';

if (Test-Path $apk) {
    Write-Host '=== SUCCESS! APK BUILT ===';
    Write-Host 'APK Location: ' $apk -ForegroundColor Green;
} else {
    Write-Host 'BUILD FAILED — CHECK TERMINAL OUTPUT.' -ForegroundColor Red;
}

