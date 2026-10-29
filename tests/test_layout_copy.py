# Shared fixtures only; test bodies are in top/ and mid/. See TESTS.md.
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
