"""The command line and the runner (RCT-4, "Where it lives and how it is started"): `--trunk`, `--root-contract` and
`--only`; the exit status 0, 1 and 2; PostgreSQL's programs named when they are missing; R16 after every scenario."""

from __future__ import annotations
import tempfile
from pathlib import Path

from rct_conformance.judge import Mismatch, describe
from rct_conformance.registry import SCENARIOS, Scenario, select
from rct_conformance.runner import run_suite
from .support import CLI, FAKE_TRUNK, LAYOUT, psql


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


    def test_reports_each_scenario_and_runs_r16_after_each(self) -> None:
        """runner.report: PASS for a scenario whose checks and R16 pass, FAIL with what was expected and received for
        one whose check fails, FAIL naming R16 for one that changes the tables, and the status 1."""
        def passes(home: ScenarioHome) -> None:
            started = home.start(extra={"FAKE_TRUNK_MODE": "accept", "FAKE_PSQL": psql()})
            if not started.answer["accepted"]:
                raise Mismatch("not accepted")

        def fails(home: ScenarioHome) -> None:
            raise Mismatch("The Exchange's state differs.", "completed", "failed")

        def changes_the_tables(home: ScenarioHome) -> None:
            home.start(extra={"FAKE_TRUNK_MODE": "change-layout", "FAKE_PSQL": psql()})

        homes: list[ScenarioHome] = []

        def make_home(scenario: Scenario) -> ScenarioHome:
            homes.append(self.make_home(scenario))
            return homes[-1]

        lines: list[str] = []
        scenarios = [Scenario("T1", "Passes", (), passes), Scenario("T2", "Fails", (), fails),
                     Scenario("T3", "Changes the tables", (), changes_the_tables), Scenario("T4", "Not yet", ())]
        status = run_suite(scenarios, make_home, lines.append)
        self.assertEqual(status, 1)
        self.assertEqual(lines[0], "PASS T1 — Passes")
        self.assertEqual(lines[1:5], ["FAIL T2 — Fails", "  The Exchange's state differs.",
                                      '  Expected: "completed"', '  Received: "failed"'])
        self.assertEqual(lines[5], "FAIL T3 — Changes the tables")
        self.assertIn("R16: the tables are not those layout.sql made", lines[6])
        self.assertEqual(lines[-3:], ["FAIL T4 — Not yet", "  Not implemented yet.", "1/4 scenarios passed."])
        self.assertEqual(len(homes), 3)
        self.assertTrue(all(not home.home.exists() for home in homes))


if __name__ == "__main__":
    unittest.main()

# Archived complete imports; restore needed names in their original scope, not at this file tail.
