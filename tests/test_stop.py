# Shared fixtures only; test bodies are in top/ and mid/. See TESTS.md.
from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))
from management_support import Fixture  # noqa: E402


class MovingClock:
    def __init__(self) -> None:
        self.value = 0.0
        self.pauses: list[float] = []

    def now(self) -> float:
        return self.value

    def pause(self, seconds: float) -> None:
        self.pauses.append(seconds)
        self.value += seconds


class Stopping(unittest.TestCase):
    def setUp(self) -> None:
        self.f = Fixture(self)


# Archived complete imports; restore needed names in their original scope, not at this file tail.
