param(
    [string]$PythonExe = ".\.venv\Scripts\python.exe",
    [switch]$Clean,
    [switch]$SmokeLaunch
)

$ErrorActionPreference = "Stop"

if (!(Test-Path -Path $PythonExe)) {
    throw "Python executable not found: $PythonExe"
}

$ffmpegBinPath = "FFmpeg\bin"
$requiredFfmpegExecutables = @("ffmpeg.exe", "ffprobe.exe")
$exePath = "dist\MMD_AutoLipTool.exe"

function Get-MatchingToolProcessIds {
    param(
        [string]$ExecutablePath
    )

    $ids = @()
    $processes = @(Get-CimInstance Win32_Process -Filter "Name='MMD_AutoLipTool.exe'" -ErrorAction SilentlyContinue)
    foreach ($process in $processes) {
        if ([string]::Equals($process.ExecutablePath, $ExecutablePath, [System.StringComparison]::OrdinalIgnoreCase)) {
            $ids += [int]$process.ProcessId
        }
    }
    return $ids
}

function Exclude-ProcessIds {
    param(
        [int[]]$ProcessIds,
        [int[]]$ExcludedIds
    )

    $ids = @()
    foreach ($processId in $ProcessIds) {
        if ($ExcludedIds -notcontains $processId) {
            $ids += $processId
        }
    }
    return $ids
}

function Stop-And-WaitForProcess {
    param(
        [int]$ProcessId,
        [string]$Context
    )

    $target = Get-Process -Id $ProcessId -ErrorAction SilentlyContinue
    if ($null -eq $target) {
        return
    }

    Stop-Process -Id $ProcessId -Force
    $targetAfterStop = Get-Process -Id $ProcessId -ErrorAction SilentlyContinue
    if ($null -eq $targetAfterStop) {
        return
    }

    $waitDeadline = (Get-Date).AddSeconds(30)
    while ((Get-Date) -lt $waitDeadline) {
        $remaining = Get-Process -Id $ProcessId -ErrorAction SilentlyContinue
        if ($null -eq $remaining) {
            return
        }
        Start-Sleep -Milliseconds 500
    }

    $remaining = Get-Process -Id $ProcessId -ErrorAction SilentlyContinue
    if ($null -ne $remaining) {
        throw "$Context cleanup failed: process did not exit within 30 seconds after Stop-Process: PID $ProcessId"
    }
}

if (!(Test-Path -Path $ffmpegBinPath -PathType Container)) {
    throw "FFmpeg bin directory not found: $ffmpegBinPath`nPlace the selected FFmpeg build bin files under .\$ffmpegBinPath before running build."
}

foreach ($exeName in $requiredFfmpegExecutables) {
    $ffmpegExePath = Join-Path $ffmpegBinPath $exeName
    if (!(Test-Path -Path $ffmpegExePath -PathType Leaf)) {
        throw "Required FFmpeg executable not found: $ffmpegExePath`nPlace the selected FFmpeg build bin files under .\$ffmpegBinPath before running build."
    }
}

if ($Clean) {
    if (Test-Path -Path "build") {
        Remove-Item -Recurse -Force "build"
    }
    if (Test-Path -Path "dist\MMD_AutoLipTool") {
        Remove-Item -Recurse -Force "dist\MMD_AutoLipTool"
    }
    if (Test-Path -Path $exePath) {
        Remove-Item -Force $exePath
    }
}

& $PythonExe -m PyInstaller --noconfirm --clean ".\MMD_AutoLipTool.spec"

if ($LASTEXITCODE -ne 0) {
    exit $LASTEXITCODE
}

if (!(Test-Path -Path $exePath)) {
    throw "Build output not found: $exePath"
}

if ($SmokeLaunch) {
    $exeFullPath = (Resolve-Path -LiteralPath $exePath).Path
    $existingProcessIds = @(Get-MatchingToolProcessIds -ExecutablePath $exeFullPath)
    $proc = Start-Process -FilePath $exeFullPath -PassThru
    Start-Sleep -Seconds 5
    $proc.Refresh()
    if ($proc.HasExited) {
        throw "Smoke launch failed: process exited early with code $($proc.ExitCode)"
    }
    Stop-And-WaitForProcess -ProcessId $proc.Id -Context "Smoke launch"

    $matchingProcessIds = @(Get-MatchingToolProcessIds -ExecutablePath $exeFullPath)
    $residualProcessIds = @(Exclude-ProcessIds -ProcessIds $matchingProcessIds -ExcludedIds $existingProcessIds)
    foreach ($processId in $residualProcessIds) {
        Stop-And-WaitForProcess -ProcessId $processId -Context "Smoke launch residual"
    }

    $remainingProcessIds = @(Exclude-ProcessIds -ProcessIds @(Get-MatchingToolProcessIds -ExecutablePath $exeFullPath) -ExcludedIds $existingProcessIds)
    if ($remainingProcessIds.Count -gt 0) {
        throw "Smoke launch cleanup failed: remaining MMD_AutoLipTool.exe process IDs: $($remainingProcessIds -join ', ')"
    }

    Write-Host "Smoke launch passed: $exePath"
}

Write-Host "Build completed (onefile): dist\MMD_AutoLipTool.exe"
