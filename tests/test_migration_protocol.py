# Shared fixtures; case bodies live in top/ and mid/. See TESTS.md.
from __future__ import annotations


import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from scripts.migration_protocol import REQUIRED, protocol  # noqa: E402


class MigrationProtocol(unittest.TestCase):
    pass  # TEST-TIER-EMPTY-SUITE; helpers remain importable.


# Archived complete imports; restore needed names in their original scope, not at this file tail.
