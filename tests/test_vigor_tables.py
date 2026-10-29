# Shared fixtures; case bodies live in top/ and mid/. See TESTS.md.
"""Subscriptions Vigor's tables in both Roots' layouts and the migration check, on a check-owned socket-only server."""

from __future__ import annotations
import copy
import json
import os
import subprocess
from typing import Any


import contextlib
import shutil
import sys
import tempfile
import unittest
import uuid
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "roots/sapling/drills"))
sys.path.insert(0, str(ROOT / "contract/conformance"))
from rct_conformance.postgres import SqlError  # noqa: E402
from scripts.check_layout import run_layout  # noqa: E402
from scripts.check_migration import Origin, run_migration  # noqa: E402
from scripts.vigor_tables import INDEX, REPORTS, RESULTS, TABLES, present, preserved, rows, seed  # noqa: E402


from scripts.sql_support import BuildInput, SqlLab, private_server  # noqa: E402

VIGOR = (ROOT / "roots/sapling/layout.sql").read_text(encoding="utf-8")
VIGOR = VIGOR[VIGOR.index("-- Subscriptions Vigor's records") :]


class OperationalBoundary(unittest.TestCase):
    pass  # TEST-TIER-EMPTY-SUITE; helpers remain importable.


class VigorTables(unittest.TestCase):
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
        temporary = tempfile.TemporaryDirectory(prefix="vigor-layout-input-")
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

    def database(self, root: str) -> str:
        name = "vg_" + uuid.uuid4().hex
        self.lab.server.createdb(name)
        self.lab.run_file(name, self.inputs.file("chat-tables.sql"))
        self.lab.run_file(name, ROOT / "roots" / root / "layout.sql")
        return name


# Archived complete imports; restore needed names in their original scope, not at this file tail.
