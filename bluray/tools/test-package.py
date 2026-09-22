"""Synthetic ZIP checks; no player, personal profile or disc inputs."""
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
import zipfile

spec = importlib.util.spec_from_file_location('package', Path(__file__).with_name('package-player.py'))
package = importlib.util.module_from_spec(spec)
spec.loader.exec_module(package)


class PackageTests(unittest.TestCase):
    def check_archive(self, changes=None, extra=None):
        data = {'mpc-hc64.ini': package.PROFILE, 'COPYING.txt': b'synthetic license'}
        if changes:
            data.update(changes)
        manifest = {'files': {n: package.digest(v) for n, v in data.items()}}
        data['package-manifest.json'] = json.dumps(manifest).encode()
        if extra:
            data.update(extra)
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / 'fixture.zip'
            with zipfile.ZipFile(path, 'x') as z:
                for name, value in data.items():
                    z.writestr('candidate/' + name, value)
            return package.verify_zip(path)

    def test_clean(self):
        self.assertEqual(len(self.check_archive()['files']), 2)

    def test_rejects_personal_profile(self):
        with self.assertRaisesRegex(ValueError, 'profile'):
            self.check_archive({'mpc-hc64.ini': b'[Settings]\nRecentFile=example'})

    def test_rejects_unlisted_file(self):
        with self.assertRaisesRegex(ValueError, 'Unexpected'):
            self.check_archive(extra={'extra.txt': b'not allowed'})

    def test_rejects_runtime_data_even_when_hashed(self):
        with self.assertRaisesRegex(ValueError, 'Private runtime'):
            self.check_archive({'bdj-data/persistent/state': b'synthetic'})

    def test_rejects_traversal(self):
        with self.assertRaisesRegex(ValueError, 'Unsafe'):
            self.check_archive({'../outside.txt': b'synthetic'})

    def test_rejects_external_runtime_and_other_profiles(self):
        for name in ('java.exe', 'madVR64.ax', 'extra.ini'):
            with self.subTest(name=name), self.assertRaisesRegex(ValueError, 'Private runtime'):
                self.check_archive({name: b'synthetic'})

    def test_rejects_changed_bytes(self):
        with self.assertRaisesRegex(ValueError, 'checksum'):
            self.check_archive(extra={'COPYING.txt': b'modified'})

    def test_rejects_build_paths(self):
        with tempfile.TemporaryDirectory() as folder:
            p = Path(folder) / 'fixture.dll'
            p.write_bytes(b'MZ\0' + ('C:' + '/Users/' + 'Example/build.pdb').encode())
            with self.assertRaisesRegex(ValueError, 'Private build path'):
                package.checked_file(p)


if __name__ == '__main__':
    unittest.main()
