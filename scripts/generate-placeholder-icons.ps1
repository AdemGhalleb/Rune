# Generate minimal placeholder icons for Tauri until brand assets exist.

$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot
$IconsDir = Join-Path $Root "apps\desktop\src-tauri\icons"

New-Item -ItemType Directory -Force -Path $IconsDir | Out-Null

Add-Type -AssemblyName System.Drawing

function Write-Icon {
    param([int]$Size, [string]$Path)
    $bitmap = New-Object System.Drawing.Bitmap $Size, $Size
    $graphics = [System.Drawing.Graphics]::FromImage($bitmap)
    $graphics.SmoothingMode = [System.Drawing.Drawing2D.SmoothingMode]::AntiAlias
    $graphics.Clear([System.Drawing.Color]::FromArgb(15, 17, 21))
    $brush = New-Object System.Drawing.SolidBrush ([System.Drawing.Color]::FromArgb(107, 138, 253))
    $fontSize = [Math]::Max(8, [int]($Size / 2.5))
    $font = New-Object System.Drawing.Font("Segoe UI", $fontSize, [System.Drawing.FontStyle]::Bold)
    $format = New-Object System.Drawing.StringFormat
    $format.Alignment = [System.Drawing.StringAlignment]::Center
    $format.LineAlignment = [System.Drawing.StringAlignment]::Center
    $rect = New-Object System.Drawing.RectangleF 0, 0, $Size, $Size
    $graphics.DrawString("R", $font, $brush, $rect, $format)
    $bitmap.Save($Path, [System.Drawing.Imaging.ImageFormat]::Png)
    $graphics.Dispose()
    $bitmap.Dispose()
}

Write-Icon -Size 32 -Path (Join-Path $IconsDir "32x32.png")
Write-Icon -Size 128 -Path (Join-Path $IconsDir "128x128.png")
Write-Icon -Size 256 -Path (Join-Path $IconsDir "128x128@2x.png")
Write-Icon -Size 256 -Path (Join-Path $IconsDir "icon.png")

Copy-Item (Join-Path $IconsDir "icon.png") (Join-Path $IconsDir "icon.ico") -Force

# icns requires macOS tooling; copy PNG as fallback for cross-platform dev on Windows.
Copy-Item (Join-Path $IconsDir "128x128.png") (Join-Path $IconsDir "icon.icns") -Force

Write-Host "Placeholder icons written to $IconsDir"
