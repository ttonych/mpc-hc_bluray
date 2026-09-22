$ErrorActionPreference = 'Stop'
$root = (Resolve-Path (Join-Path $PSScriptRoot '../..')).Path
. (Join-Path $PSScriptRoot 'Enter-BuildEnvironment.ps1')
$out = Join-Path $root 'bluray/build/tests'
New-Item -ItemType Directory -Force -Path $out | Out-Null
Push-Location $out
try {
    foreach ($name in @('java-helper','java-test','disc-storage-test')) {
        & cl.exe /nologo /EHsc /std:c++17 /W4 /O2 /utf-8 /DNOMINMAX "/Fe:$out/bluray-$name.exe" (Join-Path $root "bluray/probe/bluray-$name.cpp") /link bcrypt.lib ole32.lib
        if ($LASTEXITCODE -ne 0) { throw "Could not build $name." }
    }
    $javaFixture = Join-Path $out ('java-fixture-' + [guid]::NewGuid().ToString('N'))
    & (Join-Path $out 'bluray-java-test.exe') $javaFixture (Join-Path $out 'bluray-java-helper.exe')
    if ($LASTEXITCODE -ne 0) { throw 'Java probe regression failed.' }
    $storageFixture = Join-Path $out ('disc-storage-fixture-' + [guid]::NewGuid().ToString('N'))
    & (Join-Path $out 'bluray-disc-storage-test.exe') $storageFixture
    if ($LASTEXITCODE -ne 0) { throw 'Disc storage regression failed.' }
} finally { Pop-Location }
