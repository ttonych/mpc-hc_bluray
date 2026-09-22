# Dot-source to configure this PowerShell process only.
param([string]$NasmDirectory)
$ErrorActionPreference = 'Stop'
$vswhere = Join-Path ${env:ProgramFiles(x86)} 'Microsoft Visual Studio/Installer/vswhere.exe'
if (!(Test-Path -LiteralPath $vswhere)) { throw 'Visual Studio Installer / vswhere is required.' }
$installation = & $vswhere -latest -products '*' -version '[17.0,18.0)' -requires Microsoft.VisualStudio.Component.VC.Tools.x86.x64 -property installationPath
if (!$installation) { throw 'Visual Studio 2022 with C++ tools is required.' }
$devcmd = Join-Path $installation 'Common7/Tools/VsDevCmd.bat'
# Repeated component scripts must not keep extending PATH through VsDevCmd.
if ($env:VSCMD_ARG_TGT_ARCH -ne 'x64' -or $env:VSCMD_ARG_HOST_ARCH -ne 'x64' -or
        !$env:VCINSTALLDIR -or !(Get-Command cl.exe -ErrorAction SilentlyContinue)) {
    $variables = & $env:ComSpec /d /s /c "`"$devcmd`" -no_logo -arch=x64 -host_arch=x64 >nul && set"
    if ($LASTEXITCODE -ne 0) { throw 'Failed to initialize the Visual Studio environment.' }
    foreach ($line in $variables) {
        if ($line -match '^([^=]+)=(.*)$') {
            [Environment]::SetEnvironmentVariable($Matches[1], $Matches[2], 'Process')
        }
    }
}
if ($NasmDirectory) {
    $nasm = Join-Path $NasmDirectory 'nasm.exe'
    if (!(Test-Path -LiteralPath $nasm)) { throw "Missing NASM: $nasm" }
    if ($env:PATH.Split(';') -notcontains $NasmDirectory) { $env:PATH = "$NasmDirectory;$env:PATH" }
}
