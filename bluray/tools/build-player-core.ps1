<# Builds the normal x64 Release player, not LAV binaries or a release package. #>
param(
    [string]$NasmDirectory,
    [string]$WindowsSdk = '10.0.19041.0',
    [ValidateRange(1, 32)][int]$Jobs = 4
)
$ErrorActionPreference = 'Stop'
$root = (Resolve-Path (Join-Path $PSScriptRoot '../..')).Path
. (Join-Path $PSScriptRoot 'Enter-BuildEnvironment.ps1') -NasmDirectory $NasmDirectory
if (!(Get-Command nasm.exe -ErrorAction SilentlyContinue)) { throw 'Add NASM to PATH or use -NasmDirectory.' }
# Use the SDK found by VsDevCmd, including on hosts with a stale UCRT registry path.
$ucrt = $env:UniversalCRTSdkDir
if (!(Test-Path -LiteralPath (Join-Path $ucrt "Include/$WindowsSdk/ucrt/stdio.h"))) {
    throw "The Universal CRT for Windows SDK $WindowsSdk is not installed."
}
$logs = Join-Path $root 'bluray/diagnostics'
New-Item -ItemType Directory -Force -Path $logs | Out-Null
$log = Join-Path $logs ('player-core-' + (Get-Date -Format 'yyyyMMdd-HHmmss') + '.log')
Push-Location $root
try {
    & $env:ComSpec /d /c 'update_version.bat --quiet'
    if ($LASTEXITCODE -ne 0) { throw 'Version generation failed.' }
    # The solution supplies library ordering that a direct vcxproj build lacks.
    & MSBuild.exe 'mpc-hc.sln' /nologo "/m:$Jobs" '/t:Apps\mpc-hc' /p:Configuration=Release /p:Platform=x64 "/p:MPCHC_WINSDK_VER=$WindowsSdk" "/p:WindowsTargetPlatformVersion=$WindowsSdk" "/p:UCRTContentRoot=$ucrt" "/p:UCRTVersion=$WindowsSdk" /clp:ErrorsOnly "/flp:logfile=$log;verbosity=normal"
    if ($LASTEXITCODE -ne 0) { throw "Player core build failed. Log: $log" }
    Write-Host "Built player core. Log: $log"
    Write-Host 'LAV, translations and playback require separate checks.'
} finally {
    Pop-Location
}
