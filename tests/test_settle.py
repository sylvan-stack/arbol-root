# Shared fixtures only; test bodies are in top/ and mid/. See TESTS.md.
from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))
from management_support import Fixture  # noqa: E402


class Settling(unittest.TestCase):
    def setUp(self) -> None:
        self.f = Fixture(self)


# Archived complete imports; restore needed names in their original scope, not at this file tail.
