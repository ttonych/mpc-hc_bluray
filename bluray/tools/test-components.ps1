param([string]$JavaHome = $env:JAVA_HOME)
$ErrorActionPreference = 'Stop'
. (Join-Path $PSScriptRoot 'Enter-BuildEnvironment.ps1')
& (Join-Path $PSScriptRoot 'test-bootstrap.ps1')
foreach ($name in @('menu-components','portable-profile','disc-java','iso-opening','lav-runtime')) {
    & (Join-Path $PSScriptRoot "test-$name.ps1")
    if ($LASTEXITCODE) { throw "Failed: $name" }
}
foreach ($name in @('fork-release','bluray-compatibility','bluray-opening-settings','iso-routing','lav-menu-bridge','lav-patch-application','bluray-read-error-ui','lav-mpeg2-stills','lav-navigation-timestamps','navigation-commands','navigation-display')) {
    & python (Join-Path $PSScriptRoot "test-$name.py")
    if ($LASTEXITCODE) { throw "Failed: $name" }
}
& (Join-Path $PSScriptRoot 'test-bdj-toggle.ps1') -JavaHome $JavaHome
