# Shared fixtures; case bodies live in top/ and mid/. See TESTS.md.
"""Stopping-drill helpers act only on private, disposable processes and homes."""

from __future__ import annotations
import json
import os
import shlex
import signal
import subprocess
import tempfile
import time
from datetime import timedelta
from unittest import mock


import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'roots/sapling/drills'))
from drill_support import DrillError, wait_for  # noqa: E402
from stopping_drills import reuse_build  # noqa: E402
from stopping_support import Manager, frozen, ignored_child, stop_state  # noqa: E402
from trunk_drill_support import StandinHome, processes  # noqa: E402


class Freeze(unittest.TestCase):
    pass  # TEST-TIER-EMPTY-SUITE; helpers remain importable.


class IgnoredChild(unittest.TestCase):
    pass  # TEST-TIER-EMPTY-SUITE; helpers remain importable.


class StoppingJudgment(unittest.TestCase):
    pass  # TEST-TIER-EMPTY-SUITE; helpers remain importable.


# Archived complete imports; restore needed names in their original scope, not at this file tail.
