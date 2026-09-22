"""Package a clean manual cloud build with an explicit file list and fresh INI.

Adapted from the pinned MPC-BE allowlist/hash packaging approach. Existing ZIPs
are never overwritten. This tool does not publish releases or bundle madVR/Java.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import subprocess
import zipfile

ROOT = Path(__file__).resolve().parents[2]
NATIVE = ('bluray-4.dll', 'udfread-3.dll', 'freetype.dll', 'libxml2.dll',
          'brotlicommon.dll', 'brotlidec.dll', 'bz2.dll', 'libpng16.dll',
          'z.dll', 'iconv-2.dll', 'charset-1.dll')
LAV = ('LAVSplitter.ax', 'LAVVideo.ax', 'LAVAudio.ax', 'libbluray.dll',
       'IntelQuickSyncDecoder.dll', 'LAVFilters.Dependencies.manifest',
       'avcodec-lav-63.dll', 'avformat-lav-63.dll', 'avutil-lav-61.dll',
       'avfilter-lav-12.dll', 'swresample-lav-7.dll', 'swscale-lav-10.dll')
JARS = ('libbluray-awt-j2se-1.5.0.jar', 'libbluray-j2se-1.5.0.jar')
LICENSES = ('libbluray', 'libudfread', 'freetype', 'libxml2', 'brotli',
            'bzip2', 'libpng', 'zlib', 'libiconv', 'vcpkg-port')
PROFILE = '[Settings]\r\nBluRayMenus=1\r\nKeepHistory=0\r\nEnableWebServer=0\r\n'.encode('utf-16')
PRIVATE_PATH = re.compile(r'[A-Za-z]:[\\/]+(?:Users|dev|temp|Ghidra\d*)[\\/]', re.I)


def digest(data):
    return hashlib.sha256(data).hexdigest()


def git(*args):
    return subprocess.check_output(['git', '-C', str(ROOT), *args], text=True).strip()


def checked_file(path):
    if path.is_symlink() or not path.is_file():
        raise ValueError('Missing input or symlink: ' + path.name)
    data = path.read_bytes()
    for encoding in ('utf-8', 'utf-16-le'):
        if PRIVATE_PATH.search(data.decode(encoding, errors='ignore')):
            raise ValueError('Private build path in input: ' + path.name)
    return data


def verify_zip(path):
    with zipfile.ZipFile(path) as z:
        if z.testzip() is not None or len(z.namelist()) != len(set(z.namelist())):
            raise ValueError('Invalid ZIP or duplicate members')
        for name in z.namelist():
            p = PurePosixPath(name)
            if p.is_absolute() or '..' in p.parts or '\\' in name:
                raise ValueError('Unsafe ZIP member')
        roots = {PurePosixPath(n).parts[0] for n in z.namelist()}
        if len(roots) != 1:
            raise ValueError('Expected one package root')
        prefix = roots.pop() + '/'
        manifest = json.loads(z.read(prefix + 'package-manifest.json'))
        expected = {prefix + n for n in manifest['files']} | {prefix + 'package-manifest.json'}
        if set(z.namelist()) != expected:
            raise ValueError('Unexpected/missing package member')
        for name, sha in manifest['files'].items():
            if digest(z.read(prefix + name)) != sha:
                raise ValueError('Package checksum mismatch: ' + name)
        if z.read(prefix + 'mpc-hc64.ini') != PROFILE:
            raise ValueError('Portable profile is not clean')
        forbidden = {'.log', '.dmp', '.pdb', '.iso', '.mpcpl'}
        for name in manifest['files']:
            p = PurePosixPath(name)
            if (p.suffix.lower() in forbidden or
                    (p.suffix.lower() == '.ini' and name != 'mpc-hc64.ini') or
                    p.name.lower() in ('java.exe', 'javaw.exe', 'jvm.dll', 'madvr64.ax', 'madvr.ax') or
                    any(v in p.parts for v in ('bdj-data', 'diagnostics', 'profiles'))):
                raise ValueError('Private runtime file: ' + name)
    return manifest


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--verify', type=Path)
    args = parser.parse_args()
    if args.verify:
        manifest = verify_zip(args.verify)
        print(json.dumps({'verified': args.verify.name, 'files': len(manifest['files']), 'sha256': digest(args.verify.read_bytes())}))
        return
    if os.environ.get('GITHUB_ACTIONS') != 'true' or not os.environ.get('GITHUB_RUN_ID'):
        raise SystemExit('Public candidates require the manual cloud workflow. Use prepare-local-player.ps1 for local tests.')
    head = git('rev-parse', 'HEAD')
    if head != os.environ.get('GITHUB_SHA'):
        raise SystemExit('Checkout differs from the requested build commit')
    if git('status', '--porcelain', '--untracked-files=normal', '--ignore-submodules=dirty'):
        raise SystemExit('Uncommitted source changes; package a reviewed commit')
    subprocess.run(['python', str(ROOT / 'bluray/tools/apply-lav-patch.py')], check=True)
    runtime = ROOT / 'bluray/out/libbluray-1.5.0-x64'
    lav = ROOT / 'src/thirdparty/LAVFilters/src'
    mapping = {
        'mpc-hc64.exe': ROOT / 'bin/mpc-hc_x64/mpc-hc64.exe',
        'Lang/mpcresources.ru.dll': ROOT / 'bin/mpc-hc_x64/Lang/mpcresources.ru.dll',
        'bdj-canvas.mkv': ROOT / 'bluray/assets/bdj-canvas.mkv',
        'COPYING.txt': ROOT / 'COPYING.txt',
        'licenses/MPC-HC-Authors.txt': ROOT / 'docs/Authors.txt',
        'licenses/MPC-BE-Authors.txt': ROOT / 'bluray/ports/MPC-BE-Authors.txt',
        'licenses/LAV.txt': lav / 'COPYING',
        'licenses/FFmpeg-GPLv3.txt': lav / 'ffmpeg/COPYING.GPLv3',
        'licenses/LAV-libbluray.txt': lav / 'libbluray/COPYING',
        'licenses/IntelQuickSyncDecoder.txt': lav / 'qsdecoder/license.txt',
        'build-info/libbluray-native.json': runtime / 'build-manifest.json',
        'build-info/libbluray-java.json': runtime / 'share/java/build-manifest.json',
        'build-info/lav.json': ROOT / 'bluray/diagnostics/lav-build-manifest.json',
    }
    mapping.update({n: runtime / 'bin' / n for n in NATIVE})
    mapping.update({n: runtime / 'share/java' / n for n in JARS})
    mapping.update({'LAVFilters64/' + n: lav / 'bin_x64' / n for n in LAV})
    mapping.update({'licenses/' + n + '.txt': runtime / 'licenses' / (n + '.txt') for n in LICENSES})
    docs = ['README.md', 'README.ru.md', 'AGENTS.md', 'AGENTS.ru.md',
            'bluray/CHANGELOG.md', 'bluray/CHANGELOG.ru.md', 'bluray/sources.json', 'bluray/imports.json']
    docs += git('ls-files', 'bluray/docs', 'bluray/patches').splitlines()
    mapping.update({n: ROOT / n for n in docs})
    data = {n: checked_file(p) for n, p in sorted(mapping.items())}
    # Cross-check the native, Java and LAV outputs against their build records.
    for manifest_name, field, prefix in (
        ('build-info/libbluray-native.json', 'files', ''),
        ('build-info/libbluray-java.json', 'jars', ''),
        ('build-info/lav.json', 'files', 'LAVFilters64/'),
    ):
        record = json.loads(data[manifest_name].decode('utf-8-sig'))
        for item in record[field]:
            name = prefix + item['name']
            if name in data and digest(data[name]) != item['sha256']:
                raise ValueError('Build manifest mismatch: ' + name)
    data['mpc-hc64.ini'] = PROFILE
    run = 'https://github.com/' + os.environ['GITHUB_REPOSITORY'] + '/actions/runs/' + os.environ['GITHUB_RUN_ID']
    build = {'source_commit': head, 'source_url': 'https://github.com/' + os.environ['GITHUB_REPOSITORY'] + '/tree/' + head,
             'workflow_run': run, 'kind': 'unqualified test candidate', 'runtime_verified': False}
    data['build-manifest.json'] = json.dumps(build, indent=2).encode()
    manifest = {**build, 'files': {n: digest(v) for n, v in sorted(data.items())}}
    data['package-manifest.json'] = json.dumps(manifest, indent=2).encode()
    name = 'mpc-hc_bluray-2.8.2-bluray.1-' + head[:12] + '-x64'
    folder = ROOT / 'bluray/out/packages'
    folder.mkdir(parents=True, exist_ok=True)
    target = folder / (name + '.zip')
    with zipfile.ZipFile(target, 'x', zipfile.ZIP_DEFLATED, compresslevel=6) as z:
        for n, content in sorted(data.items()):
            z.writestr(name + '/' + n, content)
    verify_zip(target)
    sha = digest(target.read_bytes())
    with target.with_suffix('.zip.sha256').open('x', encoding='ascii') as f:
        f.write(sha + '  ' + target.name + '\n')
    print(json.dumps({'archive': target.name, 'sha256': sha, 'files': len(data)}, indent=2))


if __name__ == '__main__':
    main()
