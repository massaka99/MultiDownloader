[CmdletBinding()]
param(
    [string]$OutputDir = 'dist',
    [string]$BuildDir = 'build',
    [string]$FfmpegUrl = 'https://www.gyan.dev/ffmpeg/builds/ffmpeg-release-essentials.zip',
    [switch]$SkipDownloadFfmpeg
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

function Wait-ForKeyIfInteractive {
    if (-not [Environment]::UserInteractive) {
        return
    }
    if ([Console]::IsInputRedirected) {
        return
    }
    try {
        Write-Host 'Press any key to exit...' -ForegroundColor Yellow
        [void][Console]::ReadKey($true)
    } catch {
        Read-Host 'Press Enter to exit'
    }
}

function Invoke-PythonChecked {
    param(
        [Parameter(Mandatory = $true)]
        [string[]]$Args,
        [Parameter(Mandatory = $true)]
        [string]$Description
    )

    & python @Args
    if ($LASTEXITCODE -ne 0) {
        throw "$Description failed with exit code $LASTEXITCODE"
    }
}

function Stop-RunningApp {
    param([Parameter(Mandatory = $true)][string]$Name)

    $processes = Get-Process -Name $Name -ErrorAction SilentlyContinue
    if ($processes) {
        Write-Host "Stopping running $Name instances..." -ForegroundColor Yellow
        $processes | Stop-Process -Force -ErrorAction SilentlyContinue
        Start-Sleep -Milliseconds 400
    }

    $exePath = Join-Path $OutputDir "$Name.exe"
    if (Test-Path -LiteralPath $exePath) {
        try {
            Remove-Item -LiteralPath $exePath -Force -ErrorAction Stop
        } catch {
            Write-Warning "Unable to remove $exePath. Close any running instances and try again."
            throw
        }
    }
}

function Ensure-Directory {
    param([string]$Path)
    if (-not (Test-Path -LiteralPath $Path)) {
        New-Item -ItemType Directory -Force -Path $Path | Out-Null
    }
}

function Download-File {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Url,
        [Parameter(Mandatory = $true)]
        [string]$Destination
    )
    Write-Host "Downloading $Url" -ForegroundColor Cyan
    Invoke-WebRequest -Uri $Url -OutFile $Destination -UseBasicParsing
}

function Remove-PathWithRetry {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Path,
        [int]$Attempts = 5,
        [int]$DelayMs = 400
    )

    for ($i = 1; $i -le $Attempts; $i++) {
        if (-not (Test-Path -LiteralPath $Path)) {
            return
        }
        try {
            Remove-Item -LiteralPath $Path -Recurse -Force -ErrorAction Stop
            return
        } catch {
            if ($i -eq $Attempts) {
                throw
            }
            Start-Sleep -Milliseconds $DelayMs
        }
    }
}

function Invoke-PyInstaller {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Name,
        [Parameter(Mandatory = $true)]
        [string]$Entry
    )

    $entryPath = Join-Path $PSScriptRoot $Entry
    if (-not (Test-Path -LiteralPath $entryPath)) {
        throw "Entry script not found: $entryPath"
    }

    $pyInstallerArgs = @(
        '--clean',
        '--onefile',
        '--name', $Name,
        '--workpath', $BuildDir,
        '--specpath', $PSScriptRoot,
        '--distpath', $OutputDir
    )

    $pyInstallerArgs += $cookieArgs
    $pyInstallerArgs += $iconArgs
    $pyInstallerArgs += $ffmpegArgs
    $pyInstallerArgs += $entryPath

    $nameBuildDir = Join-Path $BuildDir $Name
    Remove-PathWithRetry -Path $nameBuildDir

    Invoke-PythonChecked -Args (@('-m', 'PyInstaller') + $pyInstallerArgs) -Description "PyInstaller build for $Name"

    Write-Host "Executable created: $OutputDir\$Name.exe" -ForegroundColor Green
}

try {
    Ensure-Directory -Path $BuildDir
    Ensure-Directory -Path $OutputDir

    $toolsDir = Join-Path $PSScriptRoot '.tools'
    Ensure-Directory -Path $toolsDir

    $projectZip = Join-Path $PSScriptRoot 'ffmpeg.zip'
    $downloadZip = Join-Path $toolsDir 'ffmpeg.zip'
    $ffmpegZip = $downloadZip
    if (Test-Path -LiteralPath $projectZip) {
        $ffmpegZip = $projectZip
    }
    $ffmpegExe = Join-Path $toolsDir 'ffmpeg.exe'
    $ffprobeExe = Join-Path $toolsDir 'ffprobe.exe'

    if (-not $SkipDownloadFfmpeg) {
        if (-not (Test-Path -LiteralPath $ffmpegZip)) {
            Download-File -Url $FfmpegUrl -Destination $downloadZip
            $ffmpegZip = $downloadZip
        }
    }

    if (-not (Test-Path -LiteralPath $ffmpegExe) -or -not (Test-Path -LiteralPath $ffprobeExe)) {
        if (-not (Test-Path -LiteralPath $ffmpegZip)) {
            throw "ffmpeg zip not found at $ffmpegZip"
        }
        $extractRoot = Join-Path $toolsDir 'ffmpeg_extract'
        if (Test-Path -LiteralPath $extractRoot) {
            Remove-Item -LiteralPath $extractRoot -Recurse -Force -ErrorAction SilentlyContinue
        }
        Expand-Archive -LiteralPath $ffmpegZip -DestinationPath $extractRoot -Force

        $ffmpegSource = Get-ChildItem -LiteralPath $extractRoot -Filter 'ffmpeg.exe' -Recurse | Select-Object -First 1
        $ffprobeSource = Get-ChildItem -LiteralPath $extractRoot -Filter 'ffprobe.exe' -Recurse | Select-Object -First 1

        if (-not $ffmpegSource) {
            throw 'ffmpeg.exe not found in the downloaded archive.'
        }
        Copy-Item -LiteralPath $ffmpegSource.FullName -Destination $ffmpegExe -Force

        if ($ffprobeSource) {
            Copy-Item -LiteralPath $ffprobeSource.FullName -Destination $ffprobeExe -Force
        }

        Remove-Item -LiteralPath $extractRoot -Recurse -Force -ErrorAction SilentlyContinue
    }

    $cookieArgs = @()
    $cookiesPath = Join-Path $PSScriptRoot 'cookies.txt'
    if (Test-Path -LiteralPath $cookiesPath) {
        $cookieArgs += @('--add-data', "$cookiesPath;.")
    } else {
        Write-Warning 'cookies.txt not found. The exe will not include default cookies.'
    }

    $iconArgs = @()
    $iconPath = Join-Path $PSScriptRoot 'app.ico'
    if (Test-Path -LiteralPath $iconPath) {
        $iconArgs += @('--icon', $iconPath)
    } else {
        Write-Warning 'app.ico not found. The exe will use the default icon.'
    }

    $ffmpegArgs = @('--add-binary', "$ffmpegExe;.")
    if (Test-Path -LiteralPath $ffprobeExe) {
        $ffmpegArgs += @('--add-binary', "$ffprobeExe;.")
    } else {
        Write-Warning 'ffprobe.exe not found. Continuing without ffprobe in the exe.'
    }

    Invoke-PythonChecked -Args @('-m', 'pip', 'install', '--upgrade', 'pip') -Description 'pip upgrade'
    Invoke-PythonChecked -Args @('-m', 'pip', 'install', '-r', 'requirements.txt') -Description 'runtime dependencies install'
    Invoke-PythonChecked -Args @('-m', 'pip', 'install', '-r', 'requirements-build.txt') -Description 'build dependencies install'

    Stop-RunningApp -Name 'MultiDownloader'

    Invoke-PyInstaller -Name 'MultiDownloader' -Entry 'multi_downloader_cli.py'

    $specPaths = @(
        'MultiDownloader.spec'
    ) | ForEach-Object { Join-Path -Path $PSScriptRoot -ChildPath $_ }

    Remove-Item -LiteralPath $BuildDir -Recurse -Force -ErrorAction SilentlyContinue
    foreach ($spec in $specPaths) {
        Remove-Item -LiteralPath $spec -Force -ErrorAction SilentlyContinue
    }

    Write-Host 'Build completed successfully.' -ForegroundColor Green
} catch {
    Write-Host ''
    Write-Host 'Build failed.' -ForegroundColor Red
    Write-Host $_.Exception.Message -ForegroundColor Red
    Wait-ForKeyIfInteractive
    exit 1
}
