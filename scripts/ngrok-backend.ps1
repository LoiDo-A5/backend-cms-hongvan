# Mở HTTPS công khai tới Django (port 8000) — dùng cho VNPAY IPN và callback công khai.
#
# Bước 0 — một lần: tạo tài khoản https://dashboard.ngrok.com → "Your Authtoken"
#   ngrok config add-authtoken <TOKEN>
#
# Bước 1 — chạy Django:  python manage.py runserver 0.0.0.0:8000
# Bước 2 — chạy script này (terminal khác):
#   .\scripts\ngrok-backend.ps1
#
# Copy URL dạng https://xxxx.ngrok-free.app → đăng ký trên cổng VNPAY:
#   IPN: https://xxxx.ngrok-free.app/api/payments/vnpay/ipn/
#   Return URL (nếu cần): https://xxxx.ngrok-free.app/api/payments/vnpay/return/
#
# ALLOWED_HOSTS: thêm suffix .ngrok-free.app (xem .env.local).

param(
    [int]$Port = 8000
)

$scriptDir = Split-Path $PSScriptRoot -Parent
$toolsNgrok = Join-Path $scriptDir 'tools\ngrok.exe'

$ngrok = Get-Command ngrok -ErrorAction SilentlyContinue
if (-not $ngrok) {
    $candidates = @(
        $toolsNgrok,
        "$env:LOCALAPPDATA\Microsoft\WinGet\Links\ngrok.exe",
        "$env:ProgramFiles\Ngrok\ngrok.exe"
    )
    foreach ($p in $candidates) {
        if (Test-Path $p) {
            $ngrok = @{ Source = $p }
            break
        }
    }
}

if (-not $ngrok) {
    Write-Host "Khong tim thay ngrok. Cai: winget install Ngrok.Ngrok" -ForegroundColor Red
    exit 1
}

$exe = if ($ngrok.Source) { $ngrok.Source } else { $ngrok.Path }
Write-Host "Dang mo tunnel toi localhost:$Port ..." -ForegroundColor Cyan
Write-Host "Neu bao loi authtoken: ngrok config add-authtoken <token tu dashboard.ngrok.com>" -ForegroundColor Yellow
& $exe http $Port
