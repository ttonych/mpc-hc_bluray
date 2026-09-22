param([ValidateSet('all','argb','menu-audio','menu-background','menu-coordinates','menu-rle','playback-clock')][string]$Case = 'all')
$ErrorActionPreference = 'Stop'
$root = (Resolve-Path (Join-Path $PSScriptRoot '../..')).Path
. (Join-Path $PSScriptRoot 'Enter-BuildEnvironment.ps1')
$cases = if ($Case -eq 'all') { @('argb','menu-audio','menu-background','menu-coordinates','menu-rle','playback-clock') } else { @($Case) }
$out = Join-Path $root 'bluray/build/tests'
New-Item -ItemType Directory -Force -Path $out | Out-Null
Push-Location $out
try {
    foreach ($name in $cases) {
        $target = Join-Path $out "bluray-$name-test.exe"
        & cl.exe /nologo /EHsc /std:c++17 /W4 /O2 /DNOMINMAX "/I$root/bluray/out/libbluray-1.5.0-x64/include" "/I$root/bluray/vendor/libbluray-1.5.0/src" "/Fe:$target" (Join-Path $root "bluray/probe/bluray-$name-test.cpp")
        if ($LASTEXITCODE -ne 0) { throw "Could not build $name test." }
        & $target
        if ($LASTEXITCODE -ne 0) { throw "$name regression failed." }
    }
} finally { Pop-Location }
