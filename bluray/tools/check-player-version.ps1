param([switch]$IncludeRussian)
$ErrorActionPreference = 'Stop'
$root = (Resolve-Path (Join-Path $PSScriptRoot '../..')).Path
$json = & python (Join-Path $PSScriptRoot 'fork_version.py')
if ($LASTEXITCODE) { throw 'Fork version source check failed.' }
$expected = $json | ConvertFrom-Json
$exe = Join-Path $root 'bin/mpc-hc_x64/mpc-hc64.exe'
$info = [Diagnostics.FileVersionInfo]::GetVersionInfo($exe)
$numericBase = '{0}.{1}.{2}' -f $info.FileMajorPart, $info.FileMinorPart, $info.FileBuildPart
if ($info.ProductVersion -cne $expected.version -or $info.ProductName -cne 'MPC-HC Blu-ray' -or $numericBase -cne $expected.base) {
    throw 'Built EXE does not match the fork/base version headers.'
}
if ($IncludeRussian) {
    $ru = [Diagnostics.FileVersionInfo]::GetVersionInfo((Join-Path $root 'bin/mpc-hc_x64/Lang/mpcresources.ru.dll'))
    $resourceVersion = '{0}.{1}.{2}.{3}' -f $ru.FileMajorPart, $ru.FileMinorPart, $ru.FileBuildPart, $ru.FilePrivatePart
    if ($resourceVersion -cne ($expected.base + '.0')) { throw 'Russian resource numeric version is incompatible.' }
}
Write-Host "Verified EXE fork version $($expected.version), numeric base $numericBase; Russian resources: $IncludeRussian"
