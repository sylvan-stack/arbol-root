# Shared fixtures; case bodies live in top/ and mid/. See TESTS.md.
from __future__ import annotations
import json
import os
from unittest import mock


import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))
from management_support import Fixture  # noqa: E402
from test_listing import record  # noqa: E402
from arbol_root.model import Refusal  # noqa: E402
from arbol_root.stop import read_exchange  # noqa: E402


class Boundary(unittest.TestCase):
    pass  # TEST-TIER-EMPTY-SUITE; helpers remain importable.


# Archived complete imports; restore needed names in their original scope, not at this file tail.
