param(
    [string]$GameDir = "",
    [string]$Lang = "ru"
)

$ErrorActionPreference = "Stop"
. (Join-Path $PSScriptRoot "game_dir.ps1")

$RepoRoot = Get-FeeBayRepoRoot
$GameDir = Get-FeeBayGameDir -GameDir $GameDir
$Release = Join-Path $RepoRoot "release"
$Resources = Join-Path $GameDir "resources"

New-Item -ItemType Directory -Force -Path $Release | Out-Null

Write-Host "Building patched app.asar from game install..."
python (Join-Path $RepoRoot "tools\patch_asar.py") --game-dir $GameDir --lang $Lang
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

$Asar = Join-Path $Resources "app.asar"
$Unpacked = Join-Path $Resources "app.asar.unpacked"

Write-Host "Copying patched app.asar to release\..."
Copy-Item $Asar (Join-Path $Release "app.asar") -Force
if (Test-Path $Unpacked) {
    $relUnpacked = Join-Path $Release "app.asar.unpacked"
    if (Test-Path $relUnpacked) { Remove-Item $relUnpacked -Recurse -Force }
    Copy-Item $Unpacked $relUnpacked -Recurse -Force
}

Write-Host "Building FeeBay_RU_Installer.exe..."
Push-Location (Join-Path $RepoRoot "tools")
try {
    pyinstaller --noconfirm --clean FeeBay_RU_Installer.spec
} finally {
    Pop-Location
}

$Exe = Join-Path $RepoRoot "tools\dist\FeeBay_RU_Installer.exe"
if (Test-Path $Exe) {
    Copy-Item $Exe (Join-Path $Release "FeeBay_RU_Installer.exe") -Force
    Write-Host "Done: $Release\FeeBay_RU_Installer.exe"
} else {
    throw "Build failed."
}
