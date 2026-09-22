<# Fetch the pinned assembler and make; use Git for Windows' MSYS shell. #>
$ErrorActionPreference = 'Stop'
$component = Split-Path $PSScriptRoot -Parent
$downloads = Join-Path $component 'downloads'
$deps = Join-Path $component 'dependencies'
New-Item -ItemType Directory -Force -Path $downloads,$deps | Out-Null
$packages = @(
    @{Name='nasm-2.16.03-win64.zip'; Url='https://www.nasm.us/pub/nasm/releasebuilds/2.16.03/win64/nasm-2.16.03-win64.zip'; Hash='3ee4782247bcb874378d02f7eab4e294a84d3d15f3f6ee2de2f47a46aa7226e6'},
    @{Name='make-4.4.1-3-x86_64.pkg.tar.zst'; Url='https://repo.msys2.org/msys/x86_64/make-4.4.1-3-x86_64.pkg.tar.zst'; Hash='af0bdba17f06fe037f0194069adaa31a8fe45f1a11381501896aea1fae37bd5d'}
)
foreach ($package in $packages) {
    $archive = Join-Path $downloads $package.Name
    if (!(Test-Path -LiteralPath $archive)) { Invoke-WebRequest -Uri $package.Url -OutFile $archive -TimeoutSec 120 }
    if ((Get-FileHash -LiteralPath $archive -Algorithm SHA256).Hash.ToLowerInvariant() -ne $package.Hash) { throw "Checksum mismatch: $($package.Name)" }
}
$nasm = Join-Path $deps 'nasm-2.16.03'
if (!(Test-Path -LiteralPath (Join-Path $nasm 'nasm.exe'))) {
    Expand-Archive -LiteralPath (Join-Path $downloads $packages[0].Name) -DestinationPath $deps
}
$make = Join-Path $deps 'msys-make'
if (!(Test-Path -LiteralPath (Join-Path $make 'usr/bin/make.exe'))) {
    New-Item -ItemType Directory -Path $make -Force | Out-Null
    & tar -xf (Join-Path $downloads $packages[1].Name) -C $make
    if ($LASTEXITCODE) { throw 'Make extraction failed.' }
}
$gitRoot = Split-Path (Split-Path (Get-Command git.exe).Source -Parent) -Parent
if (!(Test-Path -LiteralPath (Join-Path $gitRoot 'usr/bin/sh.exe'))) { throw 'Git for Windows with its MSYS shell is required.' }
$env:PATH = "$nasm;$make/usr/bin;$gitRoot/usr/bin;$env:PATH"
& (Join-Path $nasm 'nasm.exe') -v
if ($LASTEXITCODE) { throw 'NASM cannot start.' }
& (Join-Path $make 'usr/bin/make.exe') --version
if ($LASTEXITCODE) { throw 'Make cannot start with this Git for Windows MSYS runtime.' }
if ($env:GITHUB_ENV) {
    @("BLURAY_NASM=$nasm", "BLURAY_MAKE=$make/usr/bin", "BLURAY_MSYS=$gitRoot") | Out-File -FilePath $env:GITHUB_ENV -Append -Encoding utf8
}
[ordered]@{nasm=$nasm;make="$make/usr/bin";msys=$gitRoot} | ConvertTo-Json
