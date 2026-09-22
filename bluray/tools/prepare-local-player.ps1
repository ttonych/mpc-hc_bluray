<# Assemble a new isolated local test directory. Never overwrites a tested copy. #>
param([Parameter(Mandatory=$true)][string]$Destination)
$ErrorActionPreference = 'Stop'
$root = (Resolve-Path (Join-Path $PSScriptRoot '../..')).Path
$dest = [IO.Path]::GetFullPath($Destination)
if (Test-Path -LiteralPath $dest) { throw 'Choose a new empty destination name; existing test copies are preserved.' }
$runtime = Join-Path $root 'bluray/out/libbluray-1.5.0-x64'
$player = Join-Path $root 'bin/mpc-hc_x64'
$lav = Join-Path $root 'src/thirdparty/LAVFilters/src/bin_x64'
$mapping = @{
    'mpc-hc64.exe' = (Join-Path $player 'mpc-hc64.exe')
    'Lang/mpcresources.ru.dll' = (Join-Path $player 'Lang/mpcresources.ru.dll')
    'bdj-canvas.mkv' = (Join-Path $root 'bluray/assets/bdj-canvas.mkv')
    'COPYING.txt' = (Join-Path $root 'COPYING.txt')
    'licenses/MPC-BE-Authors.txt' = (Join-Path $root 'bluray/ports/MPC-BE-Authors.txt')
    'build-info/libbluray-native.json' = (Join-Path $runtime 'build-manifest.json')
    'build-info/libbluray-java.json' = (Join-Path $runtime 'share/java/build-manifest.json')
    'build-info/lav.json' = (Join-Path $root 'bluray/diagnostics/lav-build-manifest.json')
}
foreach ($name in @('bluray-4.dll','udfread-3.dll','freetype.dll','libxml2.dll','brotlicommon.dll','brotlidec.dll','bz2.dll','libpng16.dll','z.dll','iconv-2.dll','charset-1.dll')) {
    $mapping[$name] = Join-Path $runtime "bin/$name"
}
foreach ($name in @('LAVSplitter.ax','LAVVideo.ax','LAVAudio.ax','libbluray.dll','IntelQuickSyncDecoder.dll','LAVFilters.Dependencies.manifest','avcodec-lav-63.dll','avformat-lav-63.dll','avutil-lav-61.dll','avfilter-lav-12.dll','swresample-lav-7.dll','swscale-lav-10.dll')) {
    $mapping["LAVFilters64/$name"] = Join-Path $lav $name
}
foreach ($name in @('libbluray-awt-j2se-1.5.0.jar','libbluray-j2se-1.5.0.jar')) {
    $mapping[$name] = Join-Path $runtime "share/java/$name"
}
foreach ($path in $mapping.Values) { if (!(Test-Path -LiteralPath $path -PathType Leaf)) { throw "Missing input: $path" } }
New-Item -ItemType Directory -Path $dest | Out-Null
$files = @()
foreach ($name in ($mapping.Keys | Sort-Object)) {
    $target = Join-Path $dest $name
    New-Item -ItemType Directory -Force -Path (Split-Path $target -Parent) | Out-Null
    Copy-Item -LiteralPath $mapping[$name] -Destination $target
    $files += [ordered]@{name=$name;sha256=(Get-FileHash -LiteralPath $target -Algorithm SHA256).Hash.ToLowerInvariant()}
}
# Explicit seed opens the mandatory portable-profile setup on first launch.
Set-Content -LiteralPath (Join-Path $dest 'mpc-hc64.ini') -Encoding unicode -Value "[Settings]`r`n[PortableTest]`r`nFirstRunComplete=0"
$licenseDestination = Join-Path $dest 'licenses'
New-Item -ItemType Directory -Force -Path $licenseDestination | Out-Null
Get-ChildItem -LiteralPath (Join-Path $runtime 'licenses') | Copy-Item -Destination $licenseDestination -Recurse
Copy-Item -LiteralPath (Join-Path $root 'bluray/sources.json') -Destination $dest
[ordered]@{kind='local development test copy';publishable=$false;files=$files} | ConvertTo-Json -Depth 5 | Set-Content -LiteralPath (Join-Path $dest 'local-manifest.json') -Encoding utf8
Write-Host "Prepared local portable copy: $dest"
