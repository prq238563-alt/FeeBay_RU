param(
    [string]$GameDir = "",
    [string]$Lang = "ru"
)

$ErrorActionPreference = "Stop"
. (Join-Path $PSScriptRoot "game_dir.ps1")

$RepoRoot = Get-FeeBayRepoRoot
$GameDir = Get-FeeBayGameDir -GameDir $GameDir
$Resources = Join-Path $GameDir "resources"
$Asar = Join-Path $Resources "app.asar"
$Backup = Join-Path $Resources "app.asar.original"

if (-not (Test-Path $Backup)) {
    Copy-Item $Asar $Backup -Force
    Write-Host "Backup created: $Backup"
}

Get-Process -Name FeeBay -ErrorAction SilentlyContinue | Stop-Process -Force

python (Join-Path $RepoRoot "tools\patch_asar.py") --game-dir $GameDir --lang $Lang
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

$size = (Get-Item $Asar).Length
$orig = (Get-Item $Backup).Length
Write-Host "app.asar: $size bytes (original $orig bytes)"
if ($size -gt $orig * 1.15) {
    Write-Error "app.asar too large for Steam. Run tools\restore_for_steam.ps1"
    exit 1
}

Write-Host "Done. Launch FeeBay.exe to test."
