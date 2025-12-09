# build_full_apk_auto.ps1 - auto-create + build Android APK (Briefcase)

Set-StrictMode -Version Latest

$ErrorActionPreference = "Stop"

function Check-Req {
    param($name, $cmd)
    Write-Host "Checking $name..."
    try {
        & $cmd > $null 2>&1
        Write-Host "  OK: $name"
        return $true
    } catch {
        Write-Host "  MISSING: $name"
        return $false
    }
}

# 1) Environment checks
$haveJava = Check-Req "Java (java -version)" "java -version"
$haveGit  = Check-Req "Git (git --version)" "git --version"
$haveGradle = $false
try { & gradle --version > $null 2>&1; $haveGradle = $true; Write-Host "  OK: Gradle" } catch { 
    if (Test-Path "./gradlew.bat") { Write-Host "  OK: gradlew.bat found (will use wrapper)"; $haveGradle = $true } else { Write-Host "  MISSING: Gradle (or gradlew.bat)"; $haveGradle = $false }
}
$haveBriefcase = Check-Req "Briefcase (python -m briefcase --version)" "python -m briefcase --version"

if (-not ($haveJava -and $haveGit -and $haveGradle -and $haveBriefcase)) {
    Write-Host "`nOne or more prerequisites are missing. Fix the missing items and re-run this script."
    if (-not $haveJava) { Write-Host " - Install JDK 11+ and ensure 'java' is on PATH." }
    if (-not $haveGit)  { Write-Host " - Install Git and restart terminal." }
    if (-not $haveGradle) { Write-Host " - Install Gradle or ensure gradlew is present in android project." }
    if (-not $haveBriefcase) { Write-Host " - Install Briefcase: python -m pip install --user briefcase" }
    exit 1
}

# 2) Ensure Android SDK env var
if (-not $Env:ANDROID_SDK_ROOT -and -not $Env:ANDROID_HOME) {
    Write-Host "ANDROID_SDK_ROOT (or ANDROID_HOME) is not set. Please set it to your Android SDK folder and re-run." 
    Write-Host "Example: setx ANDROID_SDK_ROOT 'C:\Users\DELL\AppData\Local\Android\Sdk' (then restart PowerShell)"
    exit 1
} else {
    Write-Host "ANDROID_SDK_ROOT ok: $($Env:ANDROID_SDK_ROOT)"
}

# 3) Ensure pyproject.toml has required fields for Briefcase
$pyproject = Join-Path -Path (Get-Location) -ChildPath "pyproject.toml"
if (-not (Test-Path $pyproject)) {
    Write-Host "pyproject.toml not found in project root. Briefcase needs it. Create one or run 'briefcase create' manually." 
    exit 1
}
$toml = Get-Content $pyproject -Raw

# add license.file if only license string present
if ($toml -match '^\s*license\s*=\s*"[^"]+"' -and $toml -notmatch 'license\.(file|text)') {
    Write-Host "Adding license.file = 'LICENSE' to pyproject.toml (PEP 621 compatible)."
    $toml = $toml -replace '^\s*license\s*=\s*"([^"]+)"','license.file = "LICENSE"'
}
# ensure 'sources' includes the application package name - we try to infer package name from directory name or existing project name
# find first project table [tool.briefcase.app.<appname>]
$match = $toml -match '(?ms)^\s*\[tool\.briefcase\.app\.([^\]\s]+)\]'
if ($match) {
    $appname = $matches[1]
    # ensure sources includes a package with same root name or "sas_management"
    if ($toml -notmatch 'sources\s*=') {
        Write-Host "Adding default sources to pyproject.toml for Briefcase app [$appname]."
        # insert sources under the app table
        $toml = $toml -replace "(?ms)(^\s*\[tool\.briefcase\.app\.$appname\].*?$)",'$1`nsources = ["sas_management"]'
    } elseif ($toml -notmatch 'sas_management') {
        Write-Host "Appending 'sas_management' to sources list in pyproject.toml (if your package uses a different name, update manually)."
        $toml = $toml -replace '(?ms)(sources\s*=\s*\[)([^\]]*)(\])','$1$2, "sas_management"$3'
    }
} else {
    Write-Host "No [tool.briefcase.app.<name>] found. Briefcase config may be incomplete. Continuing but you may need to manually configure pyproject.toml."
}

# write back pyproject if changed
Set-Content -Path $pyproject -Value $toml -Encoding UTF8

# 4) Ensure LICENSE exists (briefcase warns if missing). Create placeholder if not present.
$licenseFile = Join-Path (Get-Location) "LICENSE"
if (-not (Test-Path $licenseFile)) {
    Write-Host "Creating placeholder LICENSE file."
    "Copyright (c) $(Get-Date -Format yyyy) SAS Management. All rights reserved." | Out-File -FilePath $licenseFile -Encoding utf8
}

# 5) Ensure icon present for Android: look for sas_logo.png or ask to copy existing file
$iconSrc = Join-Path (Get-Location) "sas_logo.png"
if (Test-Path $iconSrc) {
    Write-Host "Found sas_logo.png - Briefcase will include it as app icon."
} else {
    Write-Host "No sas_logo.png found in project root. If you want a custom icon, place sas_logo.png in project root before running; continuing without custom icon."
}

# 6) Run briefcase create/build/package (non-interactive) for Android (gradle backend)
try {
    Write-Host "`n==> Running: python -m briefcase create android --no-input --verbose"
    & python -m briefcase create android --no-input --verbose
    Write-Host "`n==> Running: python -m briefcase build android --no-input --verbose"
    & python -m briefcase build android --no-input --verbose
    Write-Host "`n==> Running: python -m briefcase package android --no-input --verbose"
    & python -m briefcase package android --no-input --verbose
} catch {
    Write-Host "`nERROR during Briefcase steps: $($_.Exception.Message)"
    Write-Host "Check logs in ./logs and the console output above for a detailed cause."
    exit 1
}

# 7) Locate APK
$apkPaths = Get-ChildItem -Path (Get-Location) -Recurse -Filter "app-debug.apk" -ErrorAction SilentlyContinue | Select-Object -First 1
if ($apkPaths) {
    $apkFull = $apkPaths.FullName
    Write-Host "`nSUCCESS: APK built at:`n$apkFull"
    Write-Host "You can copy this APK to your phone (adb install $apkFull) or upload for distribution."
    exit 0
} else {
    Write-Host "`nBuild finished but APK not found. Look inside android build outputs:"
    $buildPath = Join-Path (Get-Location) 'build'
    if (Test-Path $buildPath) {
        Get-ChildItem -Path $buildPath -Recurse -Force -ErrorAction SilentlyContinue | Where-Object { $_.Name -like '*apk*' } | Select-Object -First 20
    }
    exit 1
}
