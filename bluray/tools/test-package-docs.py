"""Check the real packaged manuals, Cyrillic anchors and broken-link rejection."""
from pathlib import Path
import unittest
import subprocess
from package_docs import add_documents, rewrite_links, verify_links


ROOT = Path(__file__).resolve().parents[2]
COMMIT = '0' * 40


class PackageDocsTests(unittest.TestCase):
    def test_real_manuals(self):
        names = ['README.md','README.ru.md','AGENTS.md','AGENTS.ru.md',
                 'bluray/CHANGELOG.md','bluray/CHANGELOG.ru.md','COPYING.txt']
        names += subprocess.check_output(['git','-C',str(ROOT),'ls-files','bluray/docs'],text=True).splitlines()
        data = {name: (ROOT/name).read_bytes() for name in names}
        data['licenses/MPC-HC-Authors.txt'] = b'authors'
        data['licenses/MPC-BE-Authors.txt'] = b'authors'
        add_documents(data, ROOT, COMMIT)
        # Verify Markdown and HTML together, as the ZIP packager does.
        verify_links(data)
        html = {name: value for name,value in data.items() if not name.endswith('.md')}
        verify_links(html)
        self.assertIn(b'lang="ru"', data['Readme.ru.html'])
        self.assertIn(b'bluray/docs/USAGE.ru.html#', data['Readme.ru.html'])
        self.assertIn(('id="java-для-bd-j"').encode(), data['bluray/docs/USAGE.ru.html'])
        self.assertNotIn(b'<script', b''.join(html.values()))
        self.assertIn(f'/blob/{COMMIT}/CONTRIBUTING.md'.encode(), data['Readme.html'])
        self.assertIn(b'../../Readme.html', data['bluray/docs/USAGE.html'])

    def test_broken_file_and_anchor(self):
        with self.assertRaisesRegex(ValueError, 'missing packaged link'):
            verify_links({'Readme.html': b'<a href="absent.html">link</a>'})
        with self.assertRaisesRegex(ValueError, 'missing packaged anchor'):
            verify_links({'Readme.html': b'<a href="#absent">link</a>'})

    def test_source_escape(self):
        with self.assertRaisesRegex(ValueError, 'invalid document link'):
            rewrite_links('[bad](../outside.md)', 'README.md', 'Readme.html', ROOT, COMMIT, {})


if __name__ == '__main__':
    unittest.main()
