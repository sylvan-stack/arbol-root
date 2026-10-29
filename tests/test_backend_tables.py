# Shared fixtures only; test bodies are in top/ and mid/. See TESTS.md.
"""Backend layout/copy/counter acceptance on a check-owned socket-only server."""

from __future__ import annotations

import contextlib
import shutil
import sys
import tempfile
import unittest
import uuid
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts.migration_fixtures import seed  # noqa: E402
from scripts.sql_support import BuildInput, SqlLab, private_server  # noqa: E402


class OperationalBoundary(unittest.TestCase):
    pass  # TEST-TIER-EMPTY-SUITE; helpers remain importable.


class BackendTables(unittest.TestCase):
    scope: contextlib.ExitStack
    lab: SqlLab

    @classmethod
    def setUpClass(cls) -> None:
        cls.scope = contextlib.ExitStack()
        cls.lab = cls.scope.enter_context(private_server())

    @classmethod
    def tearDownClass(cls) -> None:
        cls.scope.close()

    def setUp(self) -> None:
        temporary = tempfile.TemporaryDirectory(prefix="backend-layout-input-")
        self.addCleanup(temporary.cleanup)
        folder = Path(temporary.name)
        (folder / "layout").mkdir()
        (folder / "roots/sapling").mkdir(parents=True)
        for source, name in [
            ("contract/1/layout.sql", "chat-tables.sql"),
            ("roots/jensen/layout.sql", "root-tables.sql"),
            ("roots/jensen/migrate.sql", "migrate.sql"),
        ]:
            shutil.copy2(ROOT / source, folder / "layout" / name)
        shutil.copy2(ROOT / "roots/sapling/layout.sql", folder / "roots/sapling/layout.sql")
        self.inputs = BuildInput(folder, "jensen", "0", 1, "sapling", ("check", "chat"))

    def pair(self) -> tuple[str, str]:
        source, target = "bk_source_" + uuid.uuid4().hex, "bk_target_" + uuid.uuid4().hex
        for name in (source, target):
            self.lab.server.createdb(name)
            self.lab.run_file(name, self.inputs.file("chat-tables.sql"))
            self.lab.run_file(
                name,
                self.inputs.folder / "roots/sapling/layout.sql"
                if name == source
                else self.inputs.file("root-tables.sql"),
            )
        seed(self.lab.server, source)
        return source, target


# Archived complete imports; restore needed names in their original scope, not at this file tail.
