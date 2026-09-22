param([string]$VcpkgRoot)
$ErrorActionPreference = 'Stop'
$component = Split-Path $PSScriptRoot -Parent
$manifest = Get-Content -LiteralPath (Join-Path $component 'vcpkg.json') -Raw | ConvertFrom-Json
if (!$VcpkgRoot) { $VcpkgRoot = Join-Path $component 'build/vcpkg' }
if (!(Test-Path -LiteralPath (Join-Path $VcpkgRoot '.git'))) {
    & git clone --filter=blob:none --no-checkout https://github.com/microsoft/vcpkg.git $VcpkgRoot
    if ($LASTEXITCODE) { throw 'vcpkg clone failed.' }
    & git -C $VcpkgRoot checkout --detach $manifest.'builtin-baseline'
    if ($LASTEXITCODE) { throw 'vcpkg checkout failed.' }
}
$actual = & git -C $VcpkgRoot rev-parse HEAD
if ($LASTEXITCODE -or $actual -ne $manifest.'builtin-baseline') {
    throw 'vcpkg must match the pinned baseline; existing checkouts are not modified.'
}
if (!(Test-Path -LiteralPath (Join-Path $VcpkgRoot 'vcpkg.exe'))) {
    & (Join-Path $VcpkgRoot 'bootstrap-vcpkg.bat') -disableMetrics
    if ($LASTEXITCODE) { throw 'vcpkg bootstrap failed.' }
}
$install = Join-Path $component 'build/vcpkg_installed'
& (Join-Path $VcpkgRoot 'vcpkg.exe') install "--x-manifest-root=$component" "--x-install-root=$install" "--overlay-ports=$(Join-Path $component 'ports')" --triplet x64-windows --disable-metrics
if ($LASTEXITCODE) { throw 'vcpkg dependency build failed.' }
Write-Host "Dependencies: $install/x64-windows"
