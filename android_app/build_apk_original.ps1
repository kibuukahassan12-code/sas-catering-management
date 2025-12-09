powershell -NoProfile -ExecutionPolicy Bypass -Command "& {

  $root = 'C:\Users\DELL\Desktop\sas management system\android_app';

  if (-not (Test-Path $root)) { Write-Error \"Android project path not found: $root\"; exit 1 }

  Push-Location $root;

  try {

    Write-Host 'Working directory:' (Get-Location);



    # Ensure gradle wrapper exists (try to create if missing)

    if (-not (Test-Path '.\gradlew.bat')) {

      Write-Host 'gradlew.bat missing — attempting to create wrapper...';

      if (Get-Command gradle -ErrorAction SilentlyContinue) {

        & gradle wrapper;

      } elseif (Test-Path 'C:\Gradle\gradle-8.7\bin\gradle.bat') {

        & 'C:\Gradle\gradle-8.7\bin\gradle.bat' wrapper;

      } else {

        Write-Error 'Gradle not found (and gradlew.bat missing). Install Gradle or add it to PATH, or place gradlew.bat in project.'; exit 2;

      }

      if (-not (Test-Path '.\gradlew.bat')) { Write-Error 'Failed to produce gradlew.bat'; exit 3 }

    } else { Write-Host 'gradlew.bat exists.' }



    # Copy SAS logo into all mipmap folders so the app gets the icon (use your PNG from dist)

    $logoSrc = 'C:\Users\DELL\Desktop\sas management system\dist\sas_logo.png';

    if (-not (Test-Path $logoSrc)) {

      # Try alternative location

      $logoSrc = 'C:\Users\DELL\Desktop\sas management system\sas_logo.png';

    }

    if (Test-Path $logoSrc) {

      $resDir = Join-Path $root 'app\src\main\res';

      $mipmaps = @('mipmap-mdpi','mipmap-hdpi','mipmap-xhdpi','mipmap-xxhdpi','mipmap-xxxhdpi');

      foreach ($m in $mipmaps) {

        $d = Join-Path $resDir $m;

        if (-not (Test-Path $d)) { New-Item -ItemType Directory -Path $d -Force | Out-Null }

        Copy-Item -Path $logoSrc -Destination (Join-Path $d 'ic_launcher.png') -Force;

      }

      Write-Host 'Copied sas_logo.png to mipmap folders (ic_launcher.png).';

    } else {

      Write-Warning \"Logo not found at expected paths.`n(If you want the app icon to show, place sas_logo.png in dist folder or project root.)\";

    }



    # Run the gradle wrapper build

    Write-Host 'Starting: .\gradlew.bat assembleDebug (this may take several minutes)';

    & .\gradlew.bat assembleDebug 2>&1 | Tee-Object -Variable buildOutput;

    $exit = $LASTEXITCODE;

    if ($exit -ne 0) {

      Write-Error 'Gradle build failed. Last lines of output:';

      $buildOutput | Select-Object -Last 50 | ForEach-Object { Write-Host $_ }

      exit $exit;

    }



    # Locate APK

    $apkPath = Join-Path $root 'app\build\outputs\apk\debug\app-debug.apk';

    if (Test-Path $apkPath) {

      Write-Host ''; Write-Host '================ APK READY ================'; Write-Host \"APK Location: $apkPath\"; Write-Host '==========================================';

    } else {

      Write-Warning 'Build succeeded but APK not found at expected path. Show build log (last 200 lines):';

      $buildOutput | Select-Object -Last 200 | ForEach-Object { Write-Host $_ }

      exit 4;

    }

  } finally {

    Pop-Location;

  }

}"

