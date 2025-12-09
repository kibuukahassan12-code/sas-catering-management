import os
import subprocess
import sys

# 1. Configuration: **CRITICAL: VERIFY THIS PATH!**
# Check your C:\Program Files\Java\ folder and update the name if it's not 'jdk-17'.
JAVA_HOME_PATH = r"C:\Program Files\Java\jdk-17"

# 2. Project Root: The folder containing 'gradlew'
PROJECT_ROOT = r"C:\Users\DELL\Desktop\sas management system\android_app\android_webview_app"

# --- Execution ---

# Fixes the "Value 'C:Program FilesJavajdk-17' is invalid" error
print(f"Setting JAVA_HOME to: {JAVA_HOME_PATH}")
os.environ['JAVA_HOME'] = JAVA_HOME_PATH

# Also add to PATH
java_bin = os.path.join(JAVA_HOME_PATH, "bin")
os.environ['PATH'] = f"{java_bin};{os.environ.get('PATH', '')}"

print(f"Changing directory to: {PROJECT_ROOT}")

# Update gradle.properties to ensure correct Java path
gradle_props_path = os.path.join(PROJECT_ROOT, "gradle.properties")
# Convert Windows path to forward slashes for Gradle
java_home_gradle = JAVA_HOME_PATH.replace('\\', '/')
gradle_props_content = f"""org.gradle.java.home={java_home_gradle}
android.useAndroidX=true
android.enableJetifier=true
org.gradle.jvmargs=-Xmx2048m -Dfile.encoding=UTF-8
"""
with open(gradle_props_path, 'w', encoding='ascii') as f:
    f.write(gradle_props_content)
print(f"Updated gradle.properties with Java home: {JAVA_HOME_PATH}")

# Update local.properties
local_props_path = os.path.join(PROJECT_ROOT, "local.properties")
local_props_content = f"jdk.dir={JAVA_HOME_PATH}\n"
with open(local_props_path, 'w', encoding='ascii') as f:
    f.write(local_props_content)
print(f"Updated local.properties with JDK dir: {JAVA_HOME_PATH}")

print("Starting APK build: .\\gradlew clean assembleDebug...")

try:
    # Executes the Gradle command from the specified project root directory
    subprocess.run(
        [r".\gradlew.bat", "clean", "assembleDebug", "--no-daemon"],
        cwd=PROJECT_ROOT, 
        check=True, 
        shell=True, # Needed to properly execute .\gradlew on Windows
        encoding='utf-8'
    )
    print("\n✅ BUILD SUCCESSFUL! Your APK is ready.")
    apk_path = os.path.join(PROJECT_ROOT, r"app\build\outputs\apk\debug\app-debug.apk")
    print(f"Path: {apk_path}")
    
    # Check if file exists and show size
    if os.path.exists(apk_path):
        size_mb = os.path.getsize(apk_path) / (1024 * 1024)
        print(f"File Size: {size_mb:.2f} MB")

except subprocess.CalledProcessError as e:
    print(f"\n❌ BUILD FAILED. Check the output above for Gradle errors.")
    sys.exit(e.returncode)
except FileNotFoundError:
    print("\n❌ BUILD FAILED: 'gradlew.bat' command not found. Double-check that the PROJECT_ROOT path is correct.")
    sys.exit(1)

