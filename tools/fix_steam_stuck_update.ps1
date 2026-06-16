# Clears a stuck Steam update for FeeBay (AppID 3547880).
# Run with Steam CLOSED. Use -KillSteam to stop Steam automatically.
param(
    [string]$GameDir = "",
    [switch]$KillSteam
)

$ErrorActionPreference = "Stop"
. (Join-Path $PSScriptRoot "game_dir.ps1")

$AppId = "3547880"
$GameDir = Get-FeeBayGameDir -GameDir $GameDir
$SteamApps = Split-Path -Parent (Split-Path -Parent $GameDir)
$Resources = Join-Path $GameDir "resources"
$Asar = Join-Path $Resources "app.asar"
$Backup = Join-Path $Resources "app.asar.original"
$Manifest = Join-Path $SteamApps "appmanifest_$AppId.acf"
$Downloading = Join-Path $SteamApps "downloading\$AppId"

Write-Host "=== FeeBay: fix stuck Steam update ===" -ForegroundColor Cyan
Write-Host "Game: $GameDir"

Get-Process -Name FeeBay -ErrorAction SilentlyContinue | Stop-Process -Force
Start-Sleep -Seconds 1

$steamProcs = Get-Process -Name steam, steamwebhelper -ErrorAction SilentlyContinue
if ($steamProcs) {
    if (-not $KillSteam) {
        Write-Host ""
        Write-Host "Steam is running. Close Steam completely (tray icon -> Exit), then run:" -ForegroundColor Yellow
        Write-Host "  powershell -ExecutionPolicy Bypass -File `"$PSCommandPath`" -GameDir `"$GameDir`" -KillSteam" -ForegroundColor Yellow
        Write-Host ""
        exit 1
    }
    Write-Host "Stopping Steam..."
    $steamProcs | Stop-Process -Force
    Start-Sleep -Seconds 3
}

if (Test-Path $Backup) {
    Copy-Item $Backup $Asar -Force
    Write-Host "Restored app.asar ($((Get-Item $Asar).Length) bytes)"
}

foreach ($path in @(
    (Join-Path $Resources "_asar_extract"),
    (Join-Path $Resources "_asar_clean"),
    (Join-Path $Resources "_verify_tmp"),
    (Join-Path $Resources "_test_repack.asar"),
    (Join-Path $Resources "_test_clean.asar")
)) {
    if (Test-Path $path) {
        Remove-Item $path -Recurse -Force -ErrorAction SilentlyContinue
        Write-Host "Removed: $path"
    }
}

if (Test-Path $Downloading) {
    Remove-Item $Downloading -Recurse -Force
    Write-Host "Cleared: $Downloading"
}

if (-not (Test-Path $Manifest)) {
    throw "Manifest not found: $Manifest"
}

$content = Get-Content $Manifest -Raw -Encoding UTF8
$content = $content -replace '(?ms)\t"StagedDepots"\s*\{.*?\n\t\}', ''
$content = $content -replace '"UpdateResult"\s+"\d+"', '"UpdateResult"		"0"'
$content = $content -replace '"StagingSize"\s+"\d+"', '"StagingSize"		"0"'
$content = $content -replace '"BytesToStage"\s+"\d+"', '"BytesToStage"		"0"'
$content = $content -replace '"BytesStaged"\s+"\d+"', '"BytesStaged"		"0"'
$content = $content -replace '"BytesToDownload"\s+"\d+"', '"BytesToDownload"		"0"'
$content = $content -replace '"BytesDownloaded"\s+"\d+"', '"BytesDownloaded"		"0"'
$content = $content -replace '"StateFlags"\s+"\d+"', '"StateFlags"		"4"'

Set-Content -Path $Manifest -Value $content -Encoding UTF8 -NoNewline
Write-Host "Reset manifest: $Manifest"

Write-Host ""
Write-Host "Done." -ForegroundColor Green
Write-Host "1. Start Steam"
Write-Host "2. Update FeeBay in library"
Write-Host "3. Re-install localization from release\FeeBay_RU_Installer.exe"
