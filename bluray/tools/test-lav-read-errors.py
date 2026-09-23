"""Check actual LAV delivery under process-local read faults on synthetic clips."""
import argparse
import collections
import hashlib
import json
from pathlib import Path
import subprocess


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--probe', required=True, type=Path)
    p.add_argument('--lav', required=True, type=Path)
    p.add_argument('--fixture', required=True, type=Path)
    p.add_argument('--output', required=True, type=Path)
    a = p.parse_args()
    fixture = a.fixture.resolve()
    manifest = json.loads((fixture / 'fixture.json').read_text(encoding='utf-8'))
    for name, digest in manifest['files'].items():
        assert hashlib.sha256((fixture / name).read_bytes()).hexdigest() == digest, name
    a.output.mkdir(parents=True, exist_ok=False)
    playlist = fixture / 'BDMV/PLAYLIST/00000.mpls'
    cases = [('baseline', 'none', 0, 0), ('single-once', 'once', 0, 1048576),
             ('boundary-once', 'once', 1, 0), ('single-permanent', 'persistent', 0, 1048576),
             ('boundary-permanent', 'persistent', 1, 0), ('standalone', 'none', 0, 0)]
    results = {}
    baseline = None
    for name, mode, clip, threshold in cases:
        target = fixture / f'BDMV/STREAM/{clip:05d}.m2ts'
        prefix = a.output.resolve() / name
        run = subprocess.run([str(a.probe.resolve()), str(a.lav.resolve()),
                              str(target if name == 'standalone' else playlist), str(target),
                              mode, str(threshold), str(prefix)], capture_output=True, text=True, timeout=25)
        assert run.returncode == 0, (name, run.stdout, run.stderr)
        result = json.loads(prefix.with_suffix('.json').read_text())
        samples = prefix.with_suffix('.samples').read_bytes()
        if name == 'baseline':
            baseline = samples
            rows = [line.split(',') for line in samples.decode().splitlines()]
            assert len(rows) == 576
            assert all(int(x[0]) < int(y[0]) for x, y in zip(rows, rows[1:]))
            assert abs(int(rows[-1][1]) - int(rows[0][0]) - 240000000) <= 10
        assert result['stop_ms'] < 5000, (name, result)
        if mode == 'persistent':
            assert result['event'] == 3, (name, 'must report EC_ERRORABORT', result)
            failed = [line.split(',') for line in prefix.with_suffix('.io').read_text().splitlines()
                      if line.endswith(',23')]
            counts = collections.Counter(row[0] for row in failed)
            assert 2 <= result['injected'] <= 4 and max(counts.values()) <= 2, (name, result, counts)
            assert prefix.with_suffix('.recovered.samples').read_bytes() == baseline, name
        else:
            assert result['event'] == 1, (name, 'must report EC_COMPLETE', result)
            if name != 'standalone':
                assert samples == baseline, (name, 'payload or timestamp changed')
            else:
                assert result['samples'] == 288
            if mode == 'once':
                assert result['injected'] == 1, (name, result)
                io = [list(map(int, line.split(','))) for line in prefix.with_suffix('.io').read_text().splitlines()]
                failed = next(i for i, row in enumerate(io) if row[3] == 23)
                assert io[failed + 1][0] == io[failed][0] and io[failed + 1][3] == 0, name
        results[name] = result
        print(f'{name}: PASS ({result["samples"]} samples, {result["injected"]} injected failures)')
    results['binaries'] = {f.name: hashlib.sha256(f.read_bytes()).hexdigest()
                          for f in sorted(a.lav.glob('*')) if f.suffix.lower() in ('.ax', '.dll')}
    (a.output / 'results.json').write_text(json.dumps(results, indent=2), encoding='utf-8')


if __name__ == '__main__':
    main()
