# Test implementations moved to tests/mid/archived/contract/conformance/tests/test_cli.py.
"""The command line and the runner (RCT-4, "Where it lives and how it is started"): `--trunk`, `--root-contract` and
`--only`; the exit status 0, 1 and 2; PostgreSQL's programs named when they are missing; R16 after every scenario."""

from __future__ import annotations

import os
import shlex
import subprocess
import sys
import unittest

from rct_conformance.home import ScenarioHome
from rct_conformance.registry import Scenario

from .support import CLI, FAKE_TRUNK, LAYOUT

TRUNK = shlex.join(FAKE_TRUNK)


def suite(*args: str, path: str | None = None) -> subprocess.CompletedProcess[str]:
    env = {"HOME": os.environ.get("HOME", "/tmp"), "PATH": path or os.environ["PATH"], "LANG": "en_US.UTF-8"}
    return subprocess.run([sys.executable, "-I", "-B", str(CLI), *args], capture_output=True, text=True, env=env,
                          timeout=120, check=False)


class Cli(unittest.TestCase):
    pass  # TEST-TIER-EMPTY-SUITE; helpers remain importable.




class Runner(unittest.TestCase):
    def make_home(self, scenario: Scenario) -> ScenarioHome:
        return ScenarioHome.create(scenario.id, FAKE_TRUNK, 1, LAYOUT)






if __name__ == "__main__":
    unittest.main()

# Archived complete imports; restore needed names in their original scope, not at this file tail.
