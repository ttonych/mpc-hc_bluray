param(
    [Parameter(Mandatory=$true)][string]$JavaHome,
    [string]$Jar
)
$ErrorActionPreference = 'Stop'
$workspace = Split-Path $PSScriptRoot -Parent
if (!$Jar) { $Jar = Join-Path $workspace 'out/libbluray-1.5.0-x64/share/java/libbluray-j2se-1.5.0.jar' }
$jarPath = (Resolve-Path -LiteralPath $Jar).Path
$test = Join-Path $workspace 'probe/VideoSizeTest.java'
& (Join-Path $JavaHome 'bin/java.exe') '-Djava.awt.headless=true' --class-path $jarPath $test
if ($LASTEXITCODE) { throw 'BD-J video size regression test failed.' }
