# Script to ensure Gradle wrapper JAR exists
$wrapperJar = Join-Path $PSScriptRoot "gradle\wrapper\gradle-wrapper.jar"

if (-not (Test-Path $wrapperJar)) {
    Write-Host "Gradle wrapper JAR not found. Downloading..." -ForegroundColor Yellow
    
    $wrapperDir = Split-Path $wrapperJar
    if (-not (Test-Path $wrapperDir)) {
        New-Item -ItemType Directory -Path $wrapperDir -Force | Out-Null
    }
    
    # Download gradle-wrapper.jar from Gradle distribution
    $gradleVersion = "8.5"
    $wrapperUrl = "https://raw.githubusercontent.com/gradle/gradle/v$gradleVersion/gradle/wrapper/gradle-wrapper.jar"
    
    try {
        Write-Host "Downloading gradle-wrapper.jar..." -ForegroundColor Yellow
        Invoke-WebRequest -Uri $wrapperUrl -OutFile $wrapperJar -UseBasicParsing
        Write-Host "✓ Gradle wrapper JAR downloaded successfully" -ForegroundColor Green
    } catch {
        Write-Warning "Failed to download wrapper JAR. You may need to run 'gradle wrapper' manually."
        Write-Warning "Or download from: https://github.com/gradle/gradle/raw/v$gradleVersion/gradle/wrapper/gradle-wrapper.jar"
    }
} else {
    Write-Host "✓ Gradle wrapper JAR already exists" -ForegroundColor Green
}

