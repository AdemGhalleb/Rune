# Rune local development setup (Windows)

$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot

Write-Host "==> Setting up Rune backend..."
$Backend = Join-Path $Root "apps\backend"
Set-Location $Backend

if (-not (Test-Path ".venv")) {
    python -m venv .venv
}

& .\.venv\Scripts\python.exe -m pip install --upgrade pip
& .\.venv\Scripts\pip.exe install -r requirements.txt

Write-Host "==> Installing frontend dependencies..."
Set-Location $Root
npm install

Write-Host "==> Generating placeholder Tauri icons..."
& (Join-Path $Root "scripts\generate-placeholder-icons.ps1")

Write-Host ""
Write-Host "Setup complete."
Write-Host "  Backend:  npm run dev:backend"
Write-Host "  Frontend: npm run dev"
Write-Host "  Both:     npm run dev:all"
Write-Host ""
Write-Host "Tauri desktop (requires Rust): cd apps/desktop && npm run tauri:dev"
