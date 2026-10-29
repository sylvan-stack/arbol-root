"""A scenario's home (RCT-4.1, 4.2): its setup makes the home, the server, the Root record and the database; the
starter starts the Trunk Build's program as `arbol-root` does, with a minimal environment; R16 judges the tables after
the scenario; and closing the home leaves nothing behind. A fake Trunk (fake_trunk.py) stands for a Trunk Build."""

from __future__ import annotations
import stat
import time
import uuid
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from unittest import mock
from urllib.parse import unquote

from rct_conformance.home import DATABASE, ROUTE, ScenarioHome
from rct_conformance.judge import Mismatch, wait_until
from rct_conformance.postgres import PORT, SOCKET_PATH_LIMIT


import json
import os
import subprocess
import unittest
from typing import Any

from rct_conformance.home import ScenarioHome

from .support import FAKE_TRUNK, LAYOUT, psql


def alive(pid: int) -> bool:
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    except PermissionError:
        return True
    state = subprocess.run(["/bin/ps", "-o", "state=", "-p", str(pid)], capture_output=True, text=True).stdout
    return bool(state.strip()) and not state.strip().startswith("Z")


def group_alive(pgid: int) -> bool:
    output = subprocess.run(["/bin/ps", "-A", "-o", "pgid=,state="], capture_output=True, text=True).stdout
    return any(line.split()[0] == str(pgid) and not line.split()[1].startswith("Z")
               for line in output.splitlines() if len(line.split()) == 2)


class HomeTest(unittest.TestCase):
    def home(self, scenario: str = "T1") -> ScenarioHome:
        home = ScenarioHome.create(scenario, FAKE_TRUNK, 1, LAYOUT)
        self.addCleanup(home.close)
        return home

    def report(self, home: ScenarioHome) -> Any:
        return json.loads((home.home / "fake-trunk.json").read_text())

    @staticmethod
    def mode(name: str) -> dict[str, str]:
        return {"FAKE_TRUNK_MODE": name, "FAKE_PSQL": psql()}


class Setup(HomeTest):
    pass  # TEST-TIER-EMPTY-SUITE; helpers remain importable.


    def test_the_owners_postgresql_settings_reach_neither_the_suite_nor_the_trunk(self) -> None:
        """setup.isolated: PG… variables of the owner's shell change nothing, and the Trunk gets none of them."""
        owner = {"PGHOST": "127.0.0.1", "PGPORT": "5432", "PGUSER": "postgres", "PGDATABASE": "postgres",
                 "PGPASSWORD": "not-a-password", "PGSERVICE": "nothing", "PSQLRC": "/nonexistent"}
        with mock.patch.dict(os.environ, owner):
            home = self.home()
            self.assertEqual(home.rows("SELECT current_database() AS d"), [{"d": DATABASE}])
            home.start()
        self.assertFalse(set(self.report(home)["environment"]) & set(owner))


class Starts(HomeTest):
    pass  # TEST-TIER-EMPTY-SUITE; helpers remain importable.


class R16(HomeTest):
    pass  # TEST-TIER-EMPTY-SUITE; helpers remain importable.


class Readers(HomeTest):
    pass  # TEST-TIER-EMPTY-SUITE; helpers remain importable.


if __name__ == "__main__":
    unittest.main()

# Archived complete imports; restore needed names in their original scope, not at this file tail.
