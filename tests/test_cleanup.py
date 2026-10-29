# Shared fixtures; case bodies live in top/ and mid/. See TESTS.md.
from __future__ import annotations
import contextlib
import io
import json
import shutil
from datetime import UTC, datetime
from unittest import mock


import os
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))
from arbol_root.cleanup import cleanup  # noqa: E402
from arbol_root.model import Refusal  # noqa: E402
from arbol_root.settle import settle  # noqa: E402

from management_support import Fixture  # noqa: E402
from test_listing import record  # noqa: E402


class Cleaning(unittest.TestCase):
    def setUp(self) -> None:
        self.f = Fixture(self)

    def dot(self, number: int, suffix: str = 'new', age: float = 20) -> Path:
        folder = self.f.exchanges / ('.'+str(record(number)['exchange'])+'.'+suffix)
        folder.mkdir()
        os.utime(folder, (1000-age, 1000-age))
        return folder


# Archived complete imports; restore needed names in their original scope, not at this file tail.
