<# Local x64 prototype build. MSVC uses Schannel and the built-in AV1 decoder;
   GCC-only external codec dependencies are not included in this configuration. #>
param(
    [Parameter(Mandatory=$true)][string]$MsysRoot,
    [Parameter(Mandatory=$true)][string]$MakeDirectory,
    [string]$NasmDirectory,
    [string]$WindowsSdk = '10.0.19041.0',
    [switch]$Configure
)
$ErrorActionPreference = 'Stop'
$root = (Resolve-Path (Join-Path $PSScriptRoot '../..')).Path
$lav = Join-Path $root 'src/thirdparty/LAVFilters/src'
. (Join-Path $PSScriptRoot 'Enter-BuildEnvironment.ps1') -NasmDirectory $NasmDirectory
& python (Join-Path $PSScriptRoot 'apply-lav-patch.py')
if ($LASTEXITCODE -ne 0) { throw 'LAV source verification failed.' }
$expected = (Get-Content -Raw (Join-Path $root 'bluray/sources.json') | ConvertFrom-Json).lav
foreach ($entry in @(@('ffmpeg', $expected.ffmpeg_commit), @('libbluray', $expected.internal_libbluray_commit), @('qsdecoder', $expected.qsdecoder_commit))) {
    $actual = & git -C (Join-Path $lav $entry[0]) rev-parse HEAD
    if ($LASTEXITCODE -ne 0 -or $actual -ne $entry[1]) { throw "Unexpected $($entry[0]) revision." }
}
$env:MPCHC_MSYS = (Resolve-Path -LiteralPath $MsysRoot).Path
$env:MPCHC_GIT = Split-Path (Split-Path (Get-Command git.exe).Source -Parent) -Parent
$env:Path = "$MakeDirectory;$MsysRoot/usr/bin;" + $env:Path
$env:NUMBER_OF_PROCESSORS = '4'
$env:INCLUDE += ';' + (Join-Path $root 'src/thirdparty/zlib')
$env:LIB += ';' + (Join-Path $root 'bin/lib/Release_x64')
if (!(Test-Path (Join-Path $root 'bin/lib/Release_x64/zlib.lib'))) { throw 'Build the player core (including zlib) first.' }
$logs = Join-Path $root 'bluray/diagnostics'
New-Item -ItemType Directory -Force -Path $logs | Out-Null
Push-Location $lav
try {
    if ($Configure -or !(Test-Path 'ffmpeg/ffbuild/config.mak')) {
        & sh.exe build_ffmpeg_msvc.sh x64 release *> (Join-Path $logs 'lav-ffmpeg-configure.log')
        if ($LASTEXITCODE -ne 0 -or !(Test-Path 'ffmpeg/ffbuild/config.mak')) { throw 'FFmpeg configuration failed.' }
    }
    if ((Get-Content -Raw 'ffmpeg/ffbuild/config.mak') -notmatch '--toolchain=msvc') {
        throw 'The existing FFmpeg configuration is not MSVC. Use -Configure to select it explicitly.'
    }
    # Check make directly: the upstream wrapper can hide a failed make status.
    & make.exe -C ffmpeg -j4 *> (Join-Path $logs 'lav-ffmpeg-build.log')
    if ($LASTEXITCODE -ne 0) { throw 'FFmpeg build failed; see lav-ffmpeg-build.log.' }
    $bin = Join-Path $lav 'bin_x64'
    New-Item -ItemType Directory -Force -Path (Join-Path $bin 'lib') | Out-Null
    foreach ($folder in Get-ChildItem -LiteralPath (Join-Path $lav 'ffmpeg') -Directory -Filter 'lib*') {
        Get-ChildItem -LiteralPath $folder.FullName -Filter '*-lav-*.dll' | Copy-Item -Destination $bin
        Get-ChildItem -LiteralPath $folder.FullName -Filter '*.lib' | Copy-Item -Destination (Join-Path $bin 'lib')
    }
    & MSBuild.exe LAVFilters.sln /nologo /m:4 /p:Configuration=Release /p:Platform=x64 /p:PlatformToolset=v143 "/p:WindowsTargetPlatformVersion=$WindowsSdk" "/p:UCRTVersion=$WindowsSdk" "/p:UCRTContentRoot=$env:UniversalCRTSdkDir" /clp:ErrorsOnly "/flp:logfile=$logs/lav-player-msvc.log;verbosity=normal"
    if ($LASTEXITCODE -ne 0) { throw 'LAV build failed.' }
    [ordered]@{
        lav_commit = $expected.commit
        lav_patch_revision = (Get-Content -Raw (Join-Path $root 'bluray/patches/lav-menu-bridge.json') | ConvertFrom-Json).revision
        lav_patch_sha256 = (Get-FileHash -LiteralPath (Join-Path $root 'bluray/patches/lav-menu-bridge.patch') -Algorithm SHA256).Hash.ToLowerInvariant()
        ffmpeg_commit = $expected.ffmpeg_commit
        configuration = 'Release x64 / MSVC / Schannel'
        limitations = @('GCC-only external codec dependencies are absent', 'Not a release candidate')
        files = @(Get-ChildItem -LiteralPath $bin -File | ForEach-Object {
            [ordered]@{name=$_.Name; sha256=(Get-FileHash -LiteralPath $_.FullName -Algorithm SHA256).Hash.ToLowerInvariant()}
        })
    } | ConvertTo-Json -Depth 5 | Set-Content -Encoding utf8 (Join-Path $logs 'lav-build-manifest.json')
    Write-Host "Built local LAV prototype: $bin"
} finally { Pop-Location }
