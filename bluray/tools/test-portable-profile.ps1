$ErrorActionPreference = 'Stop'
$root = (Resolve-Path (Join-Path $PSScriptRoot '../..')).Path
. (Join-Path $PSScriptRoot 'Enter-BuildEnvironment.ps1')
$build = Join-Path $root 'bluray/build/tests/portable'
New-Item -ItemType Directory -Force -Path $build | Out-Null
$target = Join-Path $build 'portable-profile-test.exe'
$fixture = Join-Path $build ('fixture-' + [guid]::NewGuid().ToString('N'))
& cl /nologo /std:c++17 /EHsc /W4 /utf-8 (Join-Path $root 'bluray/probe/portable-profile-test.cpp') "/Fe:$target" "/Fo:$build/portable-profile-test.obj" /link advapi32.lib
if ($LASTEXITCODE) { throw 'Portable import probe compilation failed.' }
& $target $fixture
if ($LASTEXITCODE) { throw "Portable import regression failed; fixture retained: $fixture" }
