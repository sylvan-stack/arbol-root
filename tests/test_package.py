from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import tarfile
import tempfile
import unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from scripts.build import copy_layout  # noqa: E402
from scripts.package_build import archive, package  # noqa: E402
from scripts.package_support import digest, metadata, target, verify, write_manifest  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]


class Package(unittest.TestCase):
    def setUp(self) -> None:
        temporary = tempfile.TemporaryDirectory(prefix='rtm-package-')
        self.addCleanup(temporary.cleanup)
        self.base = Path(temporary.name).resolve()
        self.source, self.folder = self.base / 'source', self.base / 'package'
        self.source.mkdir()
        self.folder.mkdir()
        for name in ['src','scripts','tests','bin','contract','roots']:
            shutil.copytree(ROOT / name, self.source / name, ignore=shutil.ignore_patterns('__pycache__','*.pyc'))
        for name in ['package.json','pyproject.toml','.python-version','uv.lock','arbol-build.json','README.md']:
            shutil.copy2(ROOT / name, self.source / name)
        self.cache = self.base / 'cache'
        self.cache.mkdir()
        runtime = self.base / 'fake/python/bin'
        runtime.mkdir(parents=True)
        interpreter = runtime / 'python3.14'
        interpreter.write_text('#!/bin/sh\nif [ -n "$PACKAGE_REPORT" ]; then\n'
                               '  printf "%s\\n" "$$" "$@" > "$PACKAGE_REPORT"\nelse\n  echo 3.14.8\nfi\n')
        interpreter.chmod(0o755)
        compressed = self.cache / 'fake.tar.gz'
        with tarfile.open(compressed, 'w:gz') as bundle:
            bundle.add(runtime.parent, arcname='python')
        checksum = digest(compressed)
        compressed.rename(self.cache / (checksum+'.tar.gz'))
        pin = json.loads((self.source / 'scripts/python-distribution.json').read_text())
        pin['distributions'][target()]['sha256'] = checksum
        (self.source / 'scripts/python-distribution.json').write_text(json.dumps(pin))
        patch = mock.patch.dict(os.environ, {'ARBOL_PYTHON_ARCHIVE_CACHE':str(self.cache)})
        patch.start()
        self.addCleanup(patch.stop)

    def test_package_contains_only_own_assets_runtime_and_complete_file_hashes(self) -> None:
        """root.package"""
        with mock.patch('urllib.request.urlopen') as network:
            package(str(self.folder), root=self.source)
        network.assert_not_called()
        manifest = json.loads((self.folder / 'package-manifest.json').read_text())
        self.assertEqual((manifest['build'], manifest['candidate'], manifest['dependencies']), ('0',True,{}))
        for name in ['bin/arbol-root', 'src/arbol_root/cli.py', 'tests/standin_trunk.py', 'scripts/build.py',
                     'contract/1/layout.sql', 'contract/conformance/tests/test_layout.py',
                     'contract/conformance/specifications/03-the-chat-tables.md', 'roots/sapling/layout.sql',
                     'runtime/python/bin/python3.14']:
            self.assertEqual(manifest['files'][name], digest(self.folder / name))
        with self.assertRaisesRegex(ValueError, 'already holds'):
            package(str(self.folder), root=self.source)

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

    def test_numbered_image_is_verified_after_sql_copy_and_tampering_is_detected(self) -> None:
        """root.package-integrity"""
        record = {'component':'arbol-root','entry':'bin/arbol-root','packageVersion':'1.0.0','build':'a','root':'sapling'}
        (self.folder / 'build.json').write_text(json.dumps(record))
        with mock.patch.dict(os.environ, {'ARBOL_BUILD_DIR':str(self.folder), 'ARBOL_BUILD_NUMBER':'a'}):
            package(root=self.source)
        home = self.base / 'home'
        root_file = home / 'Library/Application Support/Arbol/roots/sapling/root.json'
        root_file.parent.mkdir(parents=True)
        root_file.write_text('{"root":"sapling", "rootContract":1}')
        layout = copy_layout(self.folder, root=self.source, home=home)
        write_manifest(self.folder, layout)
        verify(self.folder)
        record['status'] = 'working'
        (self.folder / 'build.json').write_text(json.dumps(record))
        (self.folder / 'build.log').write_text('mutable')
        (self.folder / 'last-start').write_text('mutable')
        verify(self.folder)
        path = self.folder / 'layout/chat-tables.sql'
        old = path.read_bytes()
        path.write_bytes(b'changed')
        with self.assertRaisesRegex(ValueError, 'manifest'):
            verify(self.folder)
        path.write_bytes(old)
        record['root'] = 'other'
        (self.folder / 'build.json').write_text(json.dumps(record))
        with self.assertRaisesRegex(ValueError, 'identity'):
            verify(self.folder)

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

    def test_metadata_overlap_and_bad_numbered_identity_are_refused(self) -> None:
        with self.assertRaisesRegex(ValueError, 'overlap'):
            package(str(self.source), root=self.source)
        (self.folder / 'build.json').write_text('{"component":"arbol-root", "build":"a", "root":"../x"}')
        with mock.patch.dict(os.environ, {'ARBOL_BUILD_DIR':str(self.folder), 'ARBOL_BUILD_NUMBER':'a'}):
            with self.assertRaisesRegex(ValueError,'identity'):
                package(root=self.source)
        project = self.source / 'pyproject.toml'
        project.write_text(project.read_text().replace('dependencies = []', 'dependencies = ["external"]'))
        with self.assertRaisesRegex(ValueError,'standard-library'):
            metadata(self.source)
