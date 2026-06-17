$ErrorActionPreference = "Stop"
$RepoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$Release = Join-Path $RepoRoot "release"
New-Item -ItemType Directory -Force -Path $Release | Out-Null

Write-Host "Building FeeBay_RU_Update_Toolkit.exe..."
Push-Location (Join-Path $RepoRoot "tools")
try {
    pyinstaller --noconfirm --clean FeeBay_RU_Update_Toolkit.spec
} finally {
    Pop-Location
}

$Exe = Join-Path $RepoRoot "tools\dist\FeeBay_RU_Update_Toolkit.exe"
if (-not (Test-Path $Exe)) {
    throw "Build failed."
}

Copy-Item $Exe (Join-Path $Release "FeeBay_RU_Update_Toolkit.exe") -Force
Write-Host "Done: $Release\FeeBay_RU_Update_Toolkit.exe"
