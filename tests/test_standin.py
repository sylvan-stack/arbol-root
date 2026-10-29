# Shared fixtures; case bodies live in top/ and mid/. See TESTS.md.
from __future__ import annotations
import json
import os
import subprocess
import sys
import tempfile


import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class StandIn(unittest.TestCase):
    pass  # TEST-TIER-EMPTY-SUITE; helpers remain importable.


# Archived complete imports; restore needed names in their original scope, not at this file tail.
