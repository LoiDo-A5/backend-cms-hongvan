# Tai ngrok v3 stable (Windows amd64) tu CDN chinh thuc, dat vao backend-main/tools/
# (Ban cu < 3.20 co the bi ERR_NGROK_121; can tai lai bang script nay.)
# Chay:  powershell -ExecutionPolicy Bypass -File .\scripts\install-ngrok.ps1
# Sau do DONG PowerShell, mo lai, hoac:  $env:Path += ";$PWD\tools"

$ErrorActionPreference = 'Stop'
# PSScriptRoot = .../backend-main/scripts  ->  tools = .../backend-main/tools
$backendMain = Split-Path $PSScriptRoot -Parent
$tools = Join-Path $backendMain 'tools'
if (-not (Test-Path $tools)) { New-Item -ItemType Directory -Path $tools -Force | Out-Null }

# Kenh stable (Equinox) — luon lay ban v3 moi nhat cho windows-amd64 (>= 3.20).
$zipUrl = 'https://bin.equinox.io/c/bNyj1mQVY4c/ngrok-v3-stable-windows-amd64.zip'
$zipPath = Join-Path $tools 'ngrok-download.zip'

Write-Host "Dang tai ngrok..." -ForegroundColor Cyan
Invoke-WebRequest -Uri $zipUrl -OutFile $zipPath -UseBasicParsing
Expand-Archive -Path $zipPath -DestinationPath $tools -Force
Remove-Item $zipPath -Force

$exe = Join-Path $tools 'ngrok.exe'
if (-not (Test-Path $exe)) {
    Write-Host "Loi: khong thay ngrok.exe sau khi giai nen." -ForegroundColor Red
    exit 1
}

Write-Host "OK: $exe" -ForegroundColor Green
& $exe version

$userPath = [Environment]::GetEnvironmentVariable('Path', 'User')
if ($userPath -notlike "*$tools*") {
    [Environment]::SetEnvironmentVariable('Path', "$userPath;$tools", 'User')
    Write-Host "Da them vao PATH nguoi dung: $tools" -ForegroundColor Green
    Write-Host "DONG tat ca cua so PowerShell / Cursor terminal, mo lai roi chay: ngrok version" -ForegroundColor Yellow
} else {
    Write-Host "Thu muc tools da co trong PATH." -ForegroundColor Green
}

Write-Host ""
Write-Host "Ngay trong phien nay co the chay:" -ForegroundColor Cyan
Write-Host "  `$env:Path += `";$tools`""
Write-Host "  & `"$exe`" config add-authtoken <TOKEN>"
Write-Host "  & `"$exe`" http 8000"
