# Shared fixtures; case bodies live in top/ and mid/. See TESTS.md.
"""Private qualification of optional Root-owned migration modes; no owner Root or account is used."""

from __future__ import annotations
import json


import contextlib
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from scripts.migration_modes import CAPABILITY, branch, read_modes  # noqa: E402
from scripts.migration_protocol import REQUIRED, protocol  # noqa: E402

from scripts.sql_support import BuildInput, SqlLab  # noqa: E402


class Capabilities(unittest.TestCase):
    pass  # TEST-TIER-EMPTY-SUITE; helpers remain importable.


class ChatModes(unittest.TestCase):
    scope: contextlib.ExitStack
    lab: SqlLab

    @classmethod
    def setUpClass(cls) -> None:
        from scripts.sql_support import private_server
        cls.scope = contextlib.ExitStack()
        cls.lab = cls.scope.enter_context(private_server())

    @classmethod
    def tearDownClass(cls) -> None:
        cls.scope.close()

    def inputs(self) -> BuildInput:
        from scripts.sql_support import BuildInput
        temporary = tempfile.TemporaryDirectory(prefix='fictional chat modes ')
        self.addCleanup(temporary.cleanup)
        folder = Path(temporary.name)
        (folder/'layout').mkdir()
        (folder/'roots/sapling').mkdir(parents=True)
        for source,name in [('contract/1/layout.sql','chat-tables.sql'),('roots/jensen/layout.sql','root-tables.sql'),
                            ('roots/jensen/migrate.sql','migrate.sql')]:
            shutil.copy2(ROOT/source,folder/'layout'/name)
        shutil.copy2(ROOT/'roots/sapling/layout.sql',folder/'roots/sapling/layout.sql')
        return BuildInput(folder,'jensen','0',1,'sapling',('check','chat'))


# Archived complete imports; restore needed names in their original scope, not at this file tail.
