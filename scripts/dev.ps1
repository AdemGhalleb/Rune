# Start backend and frontend together (Windows)

$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot
Set-Location $Root
node scripts/dev.js
