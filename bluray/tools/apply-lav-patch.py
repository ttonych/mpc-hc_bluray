"""Apply the pinned LAV menu adapter; refuse mismatched or edited inputs."""
import hashlib
import json
from pathlib import Path
import subprocess

root = Path(__file__).resolve().parents[2]
lav = root / 'src/thirdparty/LAVFilters/src'
manifest = json.loads((root / 'bluray/patches/lav-menu-bridge.json').read_text())
patch = root / 'bluray/patches' / manifest['patch']
assert hashlib.sha256(patch.read_bytes()).hexdigest() == manifest['sha256'], 'Patch checksum mismatch'
assert subprocess.check_output(['git', '-C', str(lav), 'rev-parse', 'HEAD'], text=True).strip() == manifest['commit'], 'LAV commit mismatch'

def checksum(path):
    return hashlib.sha256(path.read_bytes().replace(b'\r\n', b'\n')).hexdigest() if path.exists() else None

states = [checksum(lav / f['path']) for f in manifest['files']]
if states == [f['after_sha256'] for f in manifest['files']]:
    print('LAV menu adapter already applied and verified.')
elif states == [f['before_sha256'] for f in manifest['files']]:
    subprocess.run(['git', '-C', str(lav), 'apply', '--check', str(patch)], check=True)
    subprocess.run(['git', '-C', str(lav), 'apply', str(patch)], check=True)
    assert all(checksum(lav / f['path']) == f['after_sha256'] for f in manifest['files']), 'Patched LAV checksum mismatch'
    print('LAV menu adapter applied and verified.')
else:
    raise SystemExit('LAV adapter files differ from both pinned input and expected output; preserve and inspect local edits.')
