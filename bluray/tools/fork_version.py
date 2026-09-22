"""Read the fork version from the player headers; do not duplicate it in scripts."""
import json
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[2]


def read_version(root=ROOT):
    upstream = (root / 'include/version.h').read_text(encoding='utf-8-sig')
    fork = (root / 'include/BlurayVersion.h').read_text(encoding='utf-8-sig')

    def number(text, name):
        matches = re.findall(r'^#define\s+' + name + r'\s+(\d+)\s*$', text, re.M)
        if len(matches) != 1 or int(matches[0]) > 65535:
            raise ValueError('Invalid version definition: ' + name)
        return int(matches[0])

    parts = [number(upstream, 'MPC_VERSION_' + part) for part in ('MAJOR', 'MINOR', 'PATCH')]
    release = number(fork, 'MPCHC_BLURAY_RELEASE')
    if not release:
        raise ValueError('Fork releases start at 1')
    base = '.'.join(map(str, parts))
    sources = json.loads((root / 'bluray/sources.json').read_text(encoding='utf-8'))
    if sources['player']['tag'] != base:
        raise ValueError('Player header and pinned upstream base differ')
    return {'base': base, 'release': release, 'version': f'{base}-bluray.{release}'}


if __name__ == '__main__':
    print(json.dumps(read_version()))
