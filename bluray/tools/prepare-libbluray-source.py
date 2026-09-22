"""Verify/extract the pinned archive and apply the complete donor patch chain."""
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tarfile
import urllib.request

root = Path(__file__).resolve().parents[1]
pin = json.loads((root / 'sources.json').read_text(encoding='utf-8'))['menu_libbluray']
archive = root / 'downloads' / pin['archive']
archive.parent.mkdir(parents=True, exist_ok=True)
if not archive.exists():
    with urllib.request.urlopen(pin['url'], timeout=60) as response:
        data = response.read()
    if hashlib.sha256(data).hexdigest() != pin['sha256']:
        raise SystemExit('Downloaded libbluray archive checksum mismatch.')
    archive.write_bytes(data)
if hashlib.sha256(archive.read_bytes()).hexdigest() != pin['sha256']:
    raise SystemExit('Local libbluray archive checksum mismatch; preserve it for inspection.')
source = root / 'vendor' / ('libbluray-' + pin['version'])
if not source.exists():
    with tarfile.open(archive) as tar:
        tar.extractall(root / 'vendor', filter='data')
# Existing trees are checked, never extracted over local work.
for component in ('native', 'bdj-toggle'):
    subprocess.run([sys.executable, str(root / 'tools/libbluray-local-patch.py'),
                    '--source', str(source), '--component', component], check=True)
print('Verified source archive and complete native/Java patch chain.')
