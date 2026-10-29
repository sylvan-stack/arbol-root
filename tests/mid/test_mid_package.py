"""Mid-tier selections. Write or run only in an explicitly requested testing task."""
from __future__ import annotations

import test_package as _support
from test_package import (archive ,json ,mock ,os ,package ,subprocess ,target)


class Package(_support.Package):

# TEST-TIER-BEGIN tests/test_package.py::Package.test_relocated_shell_entry_execs_own_python_with_arguments_and_same_pid
    def test_relocated_shell_entry_execs_own_python_with_arguments_and_same_pid(self) -> None:
        """root.package-entry"""
        package(str(self.folder), root=self.source)
        moved = self.base / 'moved package with spaces'
        self.folder.rename(moved)
        report = self.base / 'report'
        args = ['trunks', '', 'two words', '-leading']
        proc = subprocess.Popen([str(moved / 'bin/arbol-root'), *args],
                                env={**os.environ, 'PACKAGE_REPORT':str(report)})
        self.assertEqual(proc.wait(timeout=10), 0)
        self.assertEqual(report.read_text().splitlines(), [str(proc.pid),'-I','-B',str(moved / 'bin/entry.py'),*args])
# TEST-TIER-END tests/test_package.py::Package.test_relocated_shell_entry_execs_own_python_with_arguments_and_same_pid


# TEST-TIER-BEGIN tests/test_package.py::Package.test_bad_cached_digest_and_untrusted_archive_pin_are_refused
    def test_bad_cached_digest_and_untrusted_archive_pin_are_refused(self) -> None:
        """root.package-pin"""
        pin = json.loads((self.source / 'scripts/python-distribution.json').read_text())['distributions'][target()]
        (self.cache / (pin['sha256']+'.tar.gz')).write_text('damaged')
        with mock.patch('urllib.request.urlopen') as network, self.assertRaisesRegex(ValueError,'SHA-256'):
            archive(pin)
        network.assert_not_called()
        for distribution in [{'url':'https://unrelated.invalid/python','sha256':'a'*64},
                             {'url':pin['url'], 'sha256':'bad'}]:
            with self.subTest(distribution=distribution), self.assertRaises(ValueError):
                archive(distribution)
        self.assertEqual(list(self.folder.iterdir()), [])
# TEST-TIER-END tests/test_package.py::Package.test_bad_cached_digest_and_untrusted_archive_pin_are_refused
