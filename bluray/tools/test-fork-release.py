"""Run production fork tag/feed parsing and Windows revision-script regressions."""
from pathlib import Path
import os
import shutil
import subprocess
import tempfile
import unittest

from fork_version import ROOT, read_version

BUILD = ROOT / 'bluray/build/tests/fork-release'
BUILD.mkdir(parents=True, exist_ok=True)


class ForkReleaseTests(unittest.TestCase):
    def test_production_feed(self):
        source = ROOT / 'bluray/probe/release-version-test.cpp'
        exe = BUILD / ('release-test.exe' if os.name == 'nt' else 'release-test')
        if os.name == 'nt':
            self.assertIsNotNone(shutil.which('cl'), 'Run inside Enter-BuildEnvironment.ps1')
            command = ['cl', '/nologo', '/std:c++17', '/EHsc', '/W4', '/utf-8', '/DNOMINMAX', str(source), '/Fe:' + str(exe), '/Fo:' + str(BUILD / 'release-test.obj')]
        else:
            command = ['g++', '-std=c++17', '-Wall', '-Wextra', str(source), '-o', str(exe)]
        subprocess.run(command, cwd=BUILD, check=True)
        subprocess.run([str(exe)], check=True)

    def test_single_version_source(self):
        current = read_version()
        self.assertEqual(current['version'], current['base'] + '-bluray.' + str(current['release']))
        with tempfile.TemporaryDirectory(dir=BUILD, prefix='headers-') as directory:
            root = Path(directory).resolve()
            self.assertTrue(root.is_relative_to(BUILD.resolve()))
            for name in ('include/version.h', 'include/BlurayVersion.h', 'bluray/sources.json'):
                target = root / name
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(ROOT / name, target)
            header = root / 'include/BlurayVersion.h'
            header.write_text(header.read_text().replace(f'MPCHC_BLURAY_RELEASE {current["release"]}', f'MPCHC_BLURAY_RELEASE {current["release"] + 1}'), encoding='utf-8')
            self.assertEqual(read_version(root)['version'], current['base'] + '-bluray.' + str(current['release'] + 1))
            header.write_text(header.read_text().replace(f'MPCHC_BLURAY_RELEASE {current["release"] + 1}', 'MPCHC_BLURAY_RELEASE 0'), encoding='utf-8')
            with self.assertRaises(ValueError):
                read_version(root)

    @unittest.skipUnless(os.name == 'nt', 'Actual Windows batch regression runs locally/on the manual Windows build')
    def test_fork_and_other_base_tags_do_not_reset_revision(self):
        with tempfile.TemporaryDirectory(dir=BUILD, prefix='tags-') as directory:
            root = Path(directory).resolve()
            self.assertTrue(root.is_relative_to(BUILD.resolve()))
            for name in ('include/version.h', 'update_version.bat', 'common.bat', 'src/mpc-hc/res/mpc-hc.exe.manifest.conf'):
                target = root / name
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(ROOT / name, target)
            (root / 'build').mkdir()

            def git(*args):
                return subprocess.check_output(['git', '-C', str(root), *args], stderr=subprocess.STDOUT, text=True).strip()

            git('init', '-q')
            git('config', 'user.name', 'Synthetic test')
            git('config', 'user.email', 'synthetic@example.invalid')
            git('add', '.')
            git('commit', '-qm', 'base fixture')
            base = read_version()['base']
            git('tag', '-a', base, '-m', 'numeric upstream base')
            git('commit', '--allow-empty', '-qm', 'fork change')
            git('tag', '-a', base + '-bluray.1', '-m', 'published fork fixture')
            git('commit', '--allow-empty', '-qm', 'another change')
            git('tag', '-a', '99.0.0', '-m', 'unrelated base tag')
            subprocess.run([os.environ['COMSPEC'], '/d', '/c', 'update_version.bat --quiet'], cwd=root, check=True)
            header = (root / 'build/version_rev.h').read_text()
            self.assertIn('#define MPC_VERSION_REV 2\n', header)
            self.assertIn(git('rev-parse', '--short', 'HEAD'), header)


if __name__ == '__main__':
    unittest.main()
