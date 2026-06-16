param(
    [string]$GameDir = ""
)

$ErrorActionPreference = "Stop"
. (Join-Path $PSScriptRoot "game_dir.ps1")

$GameDir = Get-FeeBayGameDir -GameDir $GameDir
$Resources = Join-Path $GameDir "resources"
$Asar = Join-Path $Resources "app.asar"
$Backup = Join-Path $Resources "app.asar.original"

Write-Host "Restoring original app.asar for Steam..."
if (-not (Test-Path $Backup)) {
    throw "Backup not found: $Backup"
}

Get-Process -Name FeeBay -ErrorAction SilentlyContinue | Stop-Process -Force
Start-Sleep -Seconds 1

Copy-Item $Backup $Asar -Force
Write-Host "Restored: $Asar ($((Get-Item $Asar).Length) bytes)"

Write-Host ""
Write-Host "Next: clear Steam stuck-update state (Steam must be closed):"
Write-Host "  powershell -ExecutionPolicy Bypass -File `"$PSScriptRoot\fix_steam_stuck_update.ps1`" -GameDir `"$GameDir`" -KillSteam"
