param(
    [string]$PythonExe = ".\.venv\Scripts\python.exe",
    [switch]$Clean,
    [switch]$SmokeLaunch
)

$ErrorActionPreference = "Stop"

if (!(Test-Path -Path $PythonExe)) {
    throw "Python executable not found: $PythonExe"
}

if ($Clean) {
    if (Test-Path -Path "build") {
        Remove-Item -Recurse -Force "build"
    }
    if (Test-Path -Path "dist\MMD_AutoLipTool") {
        Remove-Item -Recurse -Force "dist\MMD_AutoLipTool"
    }
}

& $PythonExe -m PyInstaller --noconfirm --clean ".\MMD_AutoLipTool.spec"

if ($LASTEXITCODE -ne 0) {
    exit $LASTEXITCODE
}

$exePath = "dist\MMD_AutoLipTool\MMD_AutoLipTool.exe"
if (!(Test-Path -Path $exePath)) {
    throw "Build output not found: $exePath"
}

if ($SmokeLaunch) {
    $proc = Start-Process -FilePath $exePath -PassThru
    Start-Sleep -Seconds 5
    if ($proc.HasExited) {
        throw "Smoke launch failed: process exited early with code $($proc.ExitCode)"
    }
    Stop-Process -Id $proc.Id -Force
    Write-Host "Smoke launch passed: $exePath"
}

Write-Host "Build completed (onedir): dist\MMD_AutoLipTool\"
