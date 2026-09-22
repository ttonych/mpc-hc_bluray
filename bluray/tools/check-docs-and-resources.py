"""Check paired fork docs, local links, resource translations and pinned patches.

Adapted from the recorded MPC-BE publication checks. This does not assess
translation quality, runtime compatibility or the layout of generated dialogs.
"""
import hashlib
import json
from pathlib import Path
import re
from urllib.parse import unquote, urlsplit
import polib

ROOT = Path(__file__).resolve().parents[2]
PAIRS = [('README.md', 'README.ru.md'), ('AGENTS.md', 'AGENTS.ru.md')]
PAIRS += [(f'bluray/docs/{n}.md', f'bluray/docs/{n}.ru.md')
          for n in ('DEVELOPMENT', 'PORTING', 'ROADMAP', 'USAGE', 'VALIDATION')]
PAIRS += [('bluray/CHANGELOG.md', 'bluray/CHANGELOG.ru.md')]
PAIRS += [('bluray/README.md', 'bluray/README.ru.md')]
FORMAT = re.compile(r'%[-+ #0]*\d*(?:\.\d+)?(?:I64|I32|hh|ll|h|l|z|t|j)?[diuoxXfFeEgGaAcCsSpn]')


def read(path):
    raw = path.read_bytes()
    return raw.decode('utf-16' if raw[:2] in (b'\xff\xfe', b'\xfe\xff') else 'utf-8-sig')


def main():
    errors = []
    for pair in PAIRS:
        for name in pair:
            p = ROOT / name
            if not p.is_file():
                errors.append(f'Missing paired document: {name}')
                continue
            text = read(p)
            if len(re.findall(r'^```', text, re.M)) % 2:
                errors.append(f'Unclosed code fence: {name}')
            for target in re.findall(r'\[[^\]]*\]\(([^\s)]+)\)', text):
                url = urlsplit(target)
                if not url.scheme and not url.netloc and url.path:
                    if not (p.parent / unquote(url.path)).resolve().exists():
                        errors.append(f'Missing link: {name}: {target}')
    header = read(ROOT / 'src/mpc-hc/resource.h')
    ids = {key for key, number in re.findall(r'^#define\s+(IDS_BD_\w+)\s+(\d+)', header, re.M)
           if int(number) >= 58000}
    rc = read(ROOT / 'src/mpc-hc/mpc-hc.rc')
    po_root = ROOT / 'src/mpc-hc/mpcresources/PO'
    strings = polib.pofile(str(po_root / 'mpc-hc.ru.strings.po'))
    count = 0
    for key in sorted(ids):
        entries = [e for e in strings if e.msgctxt == key and not e.obsolete]
        english = re.findall(r'^\s*' + key + r'\s+"(.*)"\s*$', rc, re.M)
        if len(entries) != 1 or len(english) != 1:
            errors.append(f'Expected one EN/RU string: {key}')
            continue
        e = entries[0]
        expected = json.loads('"' + english[0].replace('""', r'\"') + '"')
        if e.msgid != expected or not e.msgstr.strip() or 'fuzzy' in e.flags:
            errors.append(f'Missing/stale translation: {key}')
        if FORMAT.findall(e.msgid.replace('%%', '')) != FORMAT.findall(e.msgstr.replace('%%', '')):
            errors.append(f'Format arguments differ: {key}')
        count += 1
    dialogs = polib.pofile(str(po_root / 'mpc-hc.ru.dialogs.po'))
    prefixes = ('IDD_PPAGEBLURAY_', 'IDD_BD_COMPATIBILITY_', 'IDD_BD_DISCS_')
    for prefix in prefixes:
        entries = [e for e in dialogs if (e.msgctxt or '').startswith(prefix) and not e.obsolete]
        if not entries or any(not e.msgstr.strip() or 'fuzzy' in e.flags for e in entries):
            errors.append(f'Missing dialog translations: {prefix}')
    for path in sorted((ROOT / 'bluray/patches').glob('*.json')):
        manifest = json.loads(path.read_text())
        expected = manifest.get('patch_sha256') or manifest.get('sha256')
        patch = path.parent / manifest.get('patch', path.with_suffix('.patch').name)
        if expected and hashlib.sha256(patch.read_bytes()).hexdigest() != expected:
            errors.append(f'Patch checksum mismatch: {path.name}')
    imports = json.loads((ROOT / 'bluray/imports.json').read_text())
    for item in imports['files']:
        if not item.get('adapted') and hashlib.sha256((ROOT / item['path']).read_bytes()).hexdigest() != item['donor_sha256']:
            errors.append(f'Unadapted donor file changed: {item["path"]}')
    print(json.dumps({'documents': len(PAIRS) * 2, 'localized_strings': count, 'problems': errors}, indent=2))
    return bool(errors)


if __name__ == '__main__':
    raise SystemExit(main())
