param([string]$WindowsSdk = '10.0.19041.0')
$ErrorActionPreference = 'Stop'
$root = (Resolve-Path (Join-Path $PSScriptRoot '../..')).Path
$python = Join-Path $PSScriptRoot '.venv/Scripts/python.exe'
if (!(Test-Path -LiteralPath $python)) {
    throw 'Create bluray/tools/.venv and install requirements-resources.txt first.'
}
. (Join-Path $PSScriptRoot 'Enter-BuildEnvironment.ps1')
Push-Location $root
try {
    # Use upstream generation without rewriting/normalizing all tracked PO files.
    & $python -c "import os,sys; os.chdir('src/mpc-hc/mpcresources'); sys.path.insert(0,os.getcwd()); from UpdateRC import UpdateRC; UpdateRC('mpc-hc.ru',False)"
    if ($LASTEXITCODE -ne 0) { throw 'Russian resource generation failed.' }
    $logs = Join-Path $root 'bluray/diagnostics'
    New-Item -ItemType Directory -Force -Path $logs | Out-Null
    $log = Join-Path $logs ('russian-resources-' + (Get-Date -Format 'yyyyMMdd-HHmmss') + '.log')
    # Generation was completed above. Do not invoke the all-language sync target.
    & MSBuild.exe 'src/mpc-hc/mpcresources/mpcresources.vcxproj' /nologo /m:2 /t:Build '/p:Configuration=Release Russian' /p:Platform=x64 /p:BuildProjectReferences=false "/p:SolutionDir=$root/" "/p:MPCHC_WINSDK_VER=$WindowsSdk" "/p:WindowsTargetPlatformVersion=$WindowsSdk" "/p:UCRTContentRoot=$env:UniversalCRTSdkDir" "/p:UCRTVersion=$WindowsSdk" /clp:ErrorsOnly "/flp:logfile=$log;verbosity=normal"
    if ($LASTEXITCODE -ne 0) { throw "Russian resource build failed. Log: $log" }
    Write-Host "Built Russian resources. Log: $log"
} finally {
    Pop-Location
}
