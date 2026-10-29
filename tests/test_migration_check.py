# Shared fixtures; case bodies live in top/ and mid/. See TESTS.md.
from __future__ import annotations
import json
import stat
from typing import Any
from unittest import mock


import contextlib
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from scripts.check_migration import Origin, check_migration, origin, run_migration  # noqa: E402

import test_sql_support  # noqa: E402

from scripts.check_migration import Origin, origin  # noqa: E402
from scripts.sql_support import BuildInput, SqlLab, private_server  # noqa: E402


class MigrationCheck(unittest.TestCase):
    scope: contextlib.ExitStack
    lab: SqlLab

    @classmethod
    def setUpClass(cls) -> None:
        cls.scope = contextlib.ExitStack()
        cls.lab = cls.scope.enter_context(private_server())

    @classmethod
    def tearDownClass(cls) -> None:
        cls.scope.close()

    def inputs(self) -> tuple[BuildInput,Origin,Path]:
        temporary = tempfile.TemporaryDirectory(prefix='root-migration-input-')
        self.addCleanup(temporary.cleanup)
        base = Path(temporary.name)
        folder = test_sql_support.SqlSupport.image(base,older='fictionalold')
        for name in ['layout.sql','migrate.sql']:
            target = 'root-tables.sql' if name == 'layout.sql' else name
            shutil.copy2(ROOT / 'tests/fixtures/migration-root' / name,folder / 'layout' / target)
        shutil.copy2(ROOT / 'contract/1/layout.sql',folder / 'layout/chat-tables.sql')
        (folder / 'contract/1').mkdir(parents=True)
        shutil.copy2(ROOT / 'contract/1/layout.sql',folder / 'contract/1/layout.sql')
        (folder / 'roots/fictionalold').mkdir(parents=True)
        shutil.copy2(ROOT / 'tests/fixtures/migration-root/source-layout.sql',folder / 'roots/fictionalold/layout.sql')
        home = base / 'private-home'
        header = home / 'Library/Application Support/Arbol/roots/fictionalold'
        header.mkdir(parents=True)
        (header / 'root.json').write_text('{"root":"fictionalold","rootContract":1}')
        inputs = BuildInput.read(folder)
        return inputs,origin(inputs,home),home


# Archived complete imports; restore needed names in their original scope, not at this file tail.
