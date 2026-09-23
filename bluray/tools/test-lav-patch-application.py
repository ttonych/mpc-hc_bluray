"""Exercise clean apply, v3 migration, idempotence and refusal of edited LAV files."""
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile

root = Path(__file__).resolve().parents[2]
source = root / 'src/thirdparty/LAVFilters/src'
manifest = json.loads((root / 'bluray/patches/lav-menu-bridge.json').read_text())
output = root / 'bluray/build/tests'
output.mkdir(parents=True, exist_ok=True)
# Keep the temporary worktrees for diagnosis; never delete source repositories.
work = Path(tempfile.mkdtemp(prefix='lav-patch-', dir=output))
lav = work / 'lav'

def git(*args, cwd=lav):
    return subprocess.run(['git', '-C', str(cwd), *args], check=True, capture_output=True)

subprocess.run(['git', 'clone', '--shared', '--no-checkout', str(source), str(lav)], check=True,
               capture_output=True)
git('checkout', '--detach', manifest['commit'])
for folder, commit in manifest['submodule_commits'].items():
    subprocess.run(['git', 'clone', '--shared', '--no-checkout', str(source / folder), str(lav / folder)],
                   check=True, capture_output=True)
    git('checkout', '--detach', commit, cwd=lav / folder)

def apply(ok=True):
    run = subprocess.run([sys.executable, str(root / 'bluray/tools/apply-lav-patch.py'),
                          '--lav-root', str(lav)], capture_output=True, text=True)
    assert (run.returncode == 0) == ok, (run.stdout, run.stderr)

apply()
apply()
git('apply', '--reverse', str(root / 'bluray/patches' / manifest['upgrade']['patch']))
for item in manifest['files']:
    f = lav / item['path']
    actual = hashlib.sha256(f.read_bytes().replace(b'\r\n', b'\n')).hexdigest() if f.exists() else None
    assert actual == item['previous_sha256'], item['path']
apply()
apply()
victim = lav / manifest['files'][0]['path']
edited = victim.read_bytes() + b'\n// Unrelated local edit must survive.\n'
victim.write_bytes(edited)
apply(ok=False)
assert victim.read_bytes() == edited
print('LAV patch: clean apply, idempotence, v3 upgrade and edited-input refusal PASS')
