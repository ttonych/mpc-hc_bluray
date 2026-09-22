param([string]$ImagePath)
$ErrorActionPreference = 'Stop'
. (Join-Path $PSScriptRoot 'Enter-BuildEnvironment.ps1')
$root = (Resolve-Path (Join-Path $PSScriptRoot '../..')).Path
$out = Join-Path $root 'bluray/build/tests'
New-Item -ItemType Directory -Force -Path $out | Out-Null
Push-Location $out
try {
    & cl /nologo /EHsc /std:c++17 /utf-8 /D_UNICODE /DUNICODE "/I$root/src/mpc-hc" "$root/bluray/probe/bluray-iso-test.cpp" /Fe:bluray-iso-test.exe /link shlwapi.lib
    if ($LASTEXITCODE -ne 0) { throw 'ISO test build failed' }
    if ($ImagePath) { & ./bluray-iso-test.exe $ImagePath } else { & ./bluray-iso-test.exe }
    if ($LASTEXITCODE -ne 0) { throw 'ISO test failed' }
} finally { Pop-Location }
