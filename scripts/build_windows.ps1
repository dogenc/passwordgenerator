# PWGen · DGKN@Labs — Windows-Release bauen
# Aufruf: powershell -ExecutionPolicy Bypass -File scripts/build_windows.ps1

$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $PSScriptRoot
Set-Location $root

Write-Host "==> Abhängigkeiten (nur Build-Zeit)"
python -m pip install --disable-pip-version-check --upgrade pip
python -m pip install --disable-pip-version-check "pyinstaller>=6.6,<7"

Write-Host "==> Tests"
python -m unittest discover -s tests -v
python pwgen_gui.py --self-test

Write-Host "==> EXE bauen"
python -m PyInstaller --noconfirm --clean pwgen.spec

Write-Host "==> Release-Verzeichnis"
New-Item -ItemType Directory -Force -Path (Join-Path $root "Release") | Out-Null
Copy-Item -Force (Join-Path $root "dist\PWGen-DGKN-Labs.exe") (Join-Path $root "Release\PWGen-DGKN-Labs.exe")
$hash = (Get-FileHash (Join-Path $root "Release\PWGen-DGKN-Labs.exe") -Algorithm SHA256).Hash.ToLower()
"$hash  PWGen-DGKN-Labs.exe" | Out-File -Encoding ascii (Join-Path $root "Release\SHA256SUMS.txt")

Write-Host "Fertig: Release\PWGen-DGKN-Labs.exe"
