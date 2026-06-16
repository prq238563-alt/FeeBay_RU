function Get-FeeBayGameDir {
    param(
        [string]$GameDir = ""
    )

    if ($GameDir) {
        $GameDir = $GameDir.Trim().Trim('"')
        if (Test-Path (Join-Path $GameDir "FeeBay.exe")) {
            return (Resolve-Path $GameDir).Path
        }
        throw "FeeBay.exe not found in: $GameDir"
    }

    $candidates = @(
        "$env:ProgramFiles(x86)\Steam\steamapps\common\FeeBay"
        "$env:ProgramFiles\Steam\steamapps\common\FeeBay"
        "D:\SteamLibrary\steamapps\common\FeeBay"
        "E:\SteamLibrary\steamapps\common\FeeBay"
        "F:\SteamLibrary\steamapps\common\FeeBay"
    )

    foreach ($path in $candidates) {
        if (Test-Path (Join-Path $path "FeeBay.exe")) {
            return (Resolve-Path $path).Path
        }
    }

    throw @"
FeeBay installation not found.
Pass -GameDir with the folder that contains FeeBay.exe, for example:
  -GameDir 'F:\SteamLibrary\steamapps\common\FeeBay'
"@
}

function Get-FeeBayRepoRoot {
    return (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
}
