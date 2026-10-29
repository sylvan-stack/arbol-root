# Shared fixtures; case bodies live in top/ and mid/. See TESTS.md.
from __future__ import annotations


import contextlib
import json
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts.check_layout import run_layout  # noqa: E402
from scripts.layout_compatibility import earlier_build  # noqa: E402

import test_sql_support  # noqa: E402

from scripts.sql_support import BuildInput, SqlLab, private_server  # noqa: E402

OLD = """
CREATE TABLE IF NOT EXISTS notes(id integer PRIMARY KEY);
COMMENT ON TABLE notes IS 'Fictional older table';
COMMENT ON COLUMN notes.id IS 'Identity';
"""


class LayoutCompatibility(unittest.TestCase):
    scope: contextlib.ExitStack
    lab: SqlLab

    @classmethod
    def setUpClass(cls) -> None:
        cls.scope = contextlib.ExitStack()
        cls.lab = cls.scope.enter_context(private_server())

    @classmethod
    def tearDownClass(cls) -> None:
        cls.scope.close()

    def inputs(self, current: str, previous: str = OLD) -> BuildInput:
        temporary = tempfile.TemporaryDirectory(prefix='root-layout-compatibility-')
        self.addCleanup(temporary.cleanup)
        base = Path(temporary.name)
        folder = test_sql_support.SqlSupport.image(base)
        folder.rename(base / 'a')
        folder = base / 'a'
        record = json.loads((folder / 'build.json').read_text())
        record['build'] = 'a'
        (folder / 'build.json').write_text(json.dumps(record))
        shutil.copy2(ROOT / 'contract/1/layout.sql', folder / 'layout/chat-tables.sql')
        (folder / 'layout/root-tables.sql').write_text(current)
        old = base / '1'
        old.mkdir()
        shutil.copy2(folder / 'package.json', old / 'package.json')
        (old / 'build.json').write_text(json.dumps({**record,'build':'1','status':'working'}))
        (old / 'layout').mkdir()
        shutil.copy2(folder / 'layout/chat-tables.sql', old / 'layout/chat-tables.sql')
        (old / 'layout/root-tables.sql').write_text(previous)
        return BuildInput.read(folder)


# Archived complete imports; restore needed names in their original scope, not at this file tail.
