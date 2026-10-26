from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from scripts.build import copy_layout  # noqa: E402


class LayoutCopy(unittest.TestCase):
    def setUp(self) -> None:
        temporary = tempfile.TemporaryDirectory(prefix="rtm-layout-copy-")
        self.addCleanup(temporary.cleanup)
        self.base = Path(temporary.name)
        self.repo, self.folder, self.home = (self.base / n for n in ['repo', 'package', 'home'])
        self.folder.mkdir()
        (self.folder / 'package.json').write_text('{"version":"1.0.0"}')
        self.record = {'component':'arbol-root', 'entry':'bin/arbol-root', 'packageVersion':'1.0.0',
                       'build':'a', 'root':'second'}
        (self.folder / 'build.json').write_text(json.dumps(self.record))
        self.root_file = self.home / 'Library/Application Support/Arbol/roots/second/root.json'
        self.root_file.parent.mkdir(parents=True)
        self.metadata: dict[str, object] = {'root':'second','rootContract':2}
        self.write_root()
        for file, text in [('contract/2/layout.sql', '-- chat\r\nSELECT \'🌲\';\n'),
                           ('roots/second/layout.sql', '-- Root\n'), ('roots/second/migrate.sql', '-- migrate\n')]:
            path = self.repo / file
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(text.encode())

    def write_root(self) -> None:
        self.root_file.write_text(json.dumps(self.metadata))

    def copy(self) -> dict[str, object]:
        return copy_layout(self.folder, root=self.repo, home=self.home)

    def test_exact_version_and_root_files_and_no_migration_without_lineage(self) -> None:
        """root.layout-copy"""
        (self.folder / 'layout').mkdir()
        (self.folder / 'layout/migrate.sql').write_text('stale')
        self.assertEqual(self.copy(), {'root':'second', 'rootContract':2, 'grewFrom':None})
        self.assertEqual((self.folder / 'layout/chat-tables.sql').read_bytes(),
                         (self.repo / 'contract/2/layout.sql').read_bytes())
        self.assertEqual((self.folder / 'layout/root-tables.sql').read_bytes(), b'-- Root\n')
        self.assertFalse((self.folder / 'layout/migrate.sql').exists())

    def test_lineage_requires_and_copies_migration_exactly(self) -> None:
        """root.layout-lineage"""
        self.metadata['grewFrom'] = 'sapling'
        self.write_root()
        self.copy()
        self.assertEqual((self.folder / 'layout/migrate.sql').read_bytes(), b'-- migrate\n')
        (self.repo / 'roots/second/migrate.sql').unlink()
        with self.assertRaisesRegex(ValueError, 'Missing regular SQL'):
            self.copy()

    def test_every_missing_file_fails_before_any_copy(self) -> None:
        """root.layout-missing"""
        for name in ['contract/2/layout.sql', 'roots/second/layout.sql']:
            path = self.repo / name
            data = path.read_bytes()
            path.unlink()
            with self.subTest(name=name), self.assertRaisesRegex(ValueError, 'Missing regular SQL'):
                self.copy()
            self.assertFalse((self.folder / 'layout').exists())
            path.write_bytes(data)

    def test_bad_root_contract_lineage_and_identity_cannot_escape_source(self) -> None:
        """root.layout-metadata"""
        for key, bad in [('rootContract',True), ('rootContract',0), ('rootContract','../x'),
                         ('root','other'), ('grewFrom','../x'), ('grewFrom','second'), ('grewFrom',None)]:
            with self.subTest(key=key, bad=bad):
                original = self.metadata.copy()
                self.metadata[key] = bad
                self.write_root()
                with self.assertRaises(ValueError):
                    self.copy()
                self.metadata = original
        self.write_root()
        (self.folder / 'build.json').write_text(json.dumps({**self.record, 'root':'../second'}))
        with self.assertRaises(ValueError):
            self.copy()
        self.assertFalse((self.folder / 'layout').exists())
