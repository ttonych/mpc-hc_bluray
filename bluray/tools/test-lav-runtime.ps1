$ErrorActionPreference = 'Stop'
$root = (Resolve-Path (Join-Path $PSScriptRoot '../..')).Path
. (Join-Path $PSScriptRoot 'Enter-BuildEnvironment.ps1')
$out = Join-Path $root 'bluray/build/tests'
New-Item -ItemType Directory -Force -Path $out | Out-Null
Push-Location $out
try {
    & cl.exe /nologo /EHsc /std:c++17 /W4 /O2 "/I$root/include" "/I$root/src/thirdparty/LAVFilters/src/include" "/Fe:$out/lav-runtime-test.exe" "$root/bluray/probe/lav-runtime-test.cpp" /link ole32.lib strmiids.lib
    if ($LASTEXITCODE -ne 0) { throw 'LAV runtime test compilation failed.' }
    & "$out/lav-runtime-test.exe" "$root/src/thirdparty/LAVFilters/src/bin_x64" "$root/bluray/assets/bdj-canvas.mkv"
    if ($LASTEXITCODE -ne 0) { throw 'LAV runtime test failed.' }
} finally { Pop-Location }
