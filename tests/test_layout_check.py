# Shared fixtures only; test bodies are in top/ and mid/. See TESTS.md.
from __future__ import annotations

import contextlib
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import test_sql_support  # noqa: E402

from scripts.sql_support import BuildInput, SqlLab, private_server  # noqa: E402


class Statements(unittest.TestCase):
    pass  # TEST-TIER-EMPTY-SUITE; helpers remain importable.


class LayoutCheck(unittest.TestCase):
    scope: contextlib.ExitStack
    lab: SqlLab

    @classmethod
    def setUpClass(cls) -> None:
        cls.scope = contextlib.ExitStack()
        cls.lab = cls.scope.enter_context(private_server())

    @classmethod
    def tearDownClass(cls) -> None:
        cls.scope.close()

    def inputs(self, own: str | None = None) -> BuildInput:
        temporary = tempfile.TemporaryDirectory(prefix='root-layout-input-')
        self.addCleanup(temporary.cleanup)
        folder = test_sql_support.SqlSupport.image(Path(temporary.name))
        shutil.copy2(ROOT / 'contract/1/layout.sql', folder / 'layout/chat-tables.sql')
        target = folder / 'layout/root-tables.sql'
        if own is None:
            shutil.copy2(ROOT / 'tests/fixtures/migration-root/layout.sql', target)
        else:
            target.write_text(own)
        return BuildInput.read(folder)


# Archived complete imports; restore needed names in their original scope, not at this file tail.
