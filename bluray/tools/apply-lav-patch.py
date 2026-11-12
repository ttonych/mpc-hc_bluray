"""Apply the pinned LAV menu adapter; refuse mismatched or edited inputs."""
import hashlib
import json
from pathlib import Path
import subprocess
import argparse

root = Path(__file__).resolve().parents[2]
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--lav-root', type=Path, default=root / 'src/thirdparty/LAVFilters/src')
lav = parser.parse_args().lav_root.resolve()
manifest = json.loads((root / 'bluray/patches/lav-menu-bridge.json').read_text())
patch = root / 'bluray/patches' / manifest['patch']
assert hashlib.sha256(patch.read_bytes()).hexdigest() == manifest['sha256'], 'Patch checksum mismatch'
assert subprocess.check_output(['git', '-C', str(lav), 'rev-parse', 'HEAD'], text=True).strip() == manifest['commit'], 'LAV commit mismatch'
for folder, commit in manifest.get('submodule_commits', {}).items():
    assert subprocess.check_output(['git', '-C', str(lav / folder), 'rev-parse', 'HEAD'], text=True).strip() == commit, 'LAV submodule commit mismatch: ' + folder

upgrades = manifest['upgrades']
for upgrade in upgrades:
    upgrade_patch = patch.parent / upgrade['patch']
    assert hashlib.sha256(upgrade_patch.read_bytes()).hexdigest() == upgrade['sha256'], 'Upgrade patch checksum mismatch'

def file_states():
    states = []
    for item in manifest['files']:
        path = lav / item['path']
        digest = hashlib.sha256(path.read_bytes().replace(b'\r\n', b'\n')).hexdigest() if path.exists() else None
        states.append(digest)
    return states

def expected(field):
    return [item.get(field, item['after_sha256']) for item in manifest['files']]

def apply(path, target):
    subprocess.run(['git', '-C', str(lav), 'apply', '--check', str(path)], check=True)
    subprocess.run(['git', '-C', str(lav), 'apply', str(path)], check=True)
    assert file_states() == target, 'Patched LAV checksum mismatch'

states = file_states()
final = expected('after_sha256')
if states == final:
    print('LAV menu adapter already applied and verified.')
elif states == expected('before_sha256'):
    apply(patch, final)
    print('LAV menu adapter applied and verified.')
else:
    inputs = [expected(step['input_hash']) for step in upgrades]
    if states not in inputs:
        raise SystemExit('Unknown LAV adapter files; preserve and inspect local edits.')
    start = inputs.index(states)
    targets = inputs[1:] + [final]
    for step, target in zip(upgrades[start:], targets[start:]):
        apply(patch.parent / step['patch'], target)
    print('LAV menu adapter upgraded and verified.')
