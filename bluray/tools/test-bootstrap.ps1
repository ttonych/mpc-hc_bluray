<# Component checks only: this does not build the DLL/JAR or test playback. #>
$ErrorActionPreference = 'Stop'
$root = (Resolve-Path (Join-Path $PSScriptRoot '../..')).Path
. (Join-Path $PSScriptRoot 'Enter-BuildEnvironment.ps1')
Push-Location $root
try {
    $checks = @(
        @('bluray/tools/prepare-libbluray-source.py'),
        @('bluray/tools/test-libbluray-local-patch.py', '--component', 'native'),
        @('bluray/tools/test-libbluray-local-patch.py', '--component', 'bdj-toggle'),
        @('bluray/tools/test-playmark-seek.py'),
        @('bluray/tools/test-process-query-hook.py')
    )
    foreach ($arguments in $checks) {
        & python @arguments
        if ($LASTEXITCODE -ne 0) { throw "Failed: $($arguments -join ' ')" }
    }
} finally {
    Pop-Location
}
