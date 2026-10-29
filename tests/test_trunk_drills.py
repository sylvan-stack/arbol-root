# Shared fixtures only; test bodies are in top/ and mid/. See TESTS.md.
"""The installed-drill frame's private boundaries, without any owner Root or inference."""

from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'roots/sapling/drills'))
from trunk_drill_support import (  # noqa: E402
    StandinHome,
)


class PrivateDriver(unittest.TestCase):
    def setUp(self) -> None:
        temporary = tempfile.TemporaryDirectory(prefix='private-drill-fixture-')
        self.addCleanup(temporary.cleanup)
        self.home = Path(temporary.name)
        self.launcher = self.home/'installed-trunk'
        self.launcher.write_text('#!/bin/sh\nexit 7\n')
        self.launcher.chmod(0o700)
        self.fixture = StandinHome(self.launcher,'selftest plain')
        self.addCleanup(self.fixture.close)


class ProcessAndRows(unittest.TestCase):
    pass  # TEST-TIER-EMPTY-SUITE; helpers remain importable.


# Archived complete imports; restore needed names in their original scope, not at this file tail.
