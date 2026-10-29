# Shared fixtures; case bodies live in top/ and mid/. See TESTS.md.
from __future__ import annotations
import os
import signal
import subprocess
import tempfile
import time


import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))
from arbol_root.input import parse  # noqa: E402
from arbol_root.model import Refusal  # noqa: E402


EXCHANGE = '7f3a2c1e-4b5d-4e6f-8a9b-0c1d2e3f4a5b'


class ManagementInput(unittest.TestCase):

    pass  # TEST-TIER-EMPTY-SUITE; helpers remain importable.


class ProcessFixture(unittest.TestCase):
    pass  # TEST-TIER-EMPTY-SUITE; helpers remain importable.

# Archived complete imports; restore needed names in their original scope, not at this file tail.
