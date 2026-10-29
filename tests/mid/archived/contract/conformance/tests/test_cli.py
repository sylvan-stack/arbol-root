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
    def test_without_initdb_on_the_search_path_it_ends_with_2_and_names_it(self) -> None:
        """cli.programs: with psql, pg_ctl and createdb but no initdb on the search path, the suite ends with 2
        before any scenario starts and names initdb."""
        with tempfile.TemporaryDirectory(prefix="rct-path-") as folder:
            for name in ("psql", "pg_ctl", "createdb"):
                found = Path(psql()).parent / name
                os.symlink(found, Path(folder) / name)
            result = suite("--trunk", TRUNK, "--root-contract", "1", path=f"{folder}:/usr/bin:/bin")
        self.assertEqual(result.returncode, 2, result.stdout + result.stderr)
        self.assertIn("missing from the search path: initdb.", result.stderr)
        self.assertEqual(result.stdout, "")

    def test_wrong_input_ends_with_2_and_says_what_is_wrong(self) -> None:
        """cli.input: an unknown option, a missing or doubled option, a Trunk that cannot be run, a version without
        layout.sql, an unknown scenario, or R16 alone."""
        cases = {
            "an unknown option": (["--trunk", TRUNK, "--root-contract", "1", "--fast"], "Unknown option: --fast"),
            "no --trunk": (["--root-contract", "1"], "Give --trunk."),
            "no --root-contract": (["--trunk", TRUNK], "Give --root-contract."),
            "--trunk twice": (["--trunk", TRUNK, "--trunk", TRUNK, "--root-contract", "1"], "only once"),
            "a Trunk that is not there": (["--trunk", "/nonexistent/arbol-trunk-trivial", "--root-contract", "1"],
                                          "does not exist or cannot be run"),
            "a Trunk not on the search path": (["--trunk", "arbol-trunk-nothing", "--root-contract", "1"],
                                               "is not on the search path"),
            "version 0": (["--trunk", TRUNK, "--root-contract", "0"], "such as 1, not 0"),
            "version 2": (["--trunk", TRUNK, "--root-contract", "2"], "version 2 has no layout.sql"),
            "an unknown scenario": (["--trunk", TRUNK, "--root-contract", "1", "--only", "R1,R99"],
                                    "Unknown scenario: R99"),
            "R16 alone": (["--trunk", TRUNK, "--root-contract", "1", "--only", "R16"], "runs after every scenario"),
        }
        for name, (args, message) in cases.items():
            with self.subTest(name):
                result = suite(*args)
                self.assertEqual(result.returncode, 2, result.stdout + result.stderr)
                self.assertIn(message, result.stderr)
                self.assertIn("Usage: rct-conformance.py", result.stderr)

    def test_a_whole_run_lists_every_scenario_and_reports_failures(self) -> None:
        """cli.whole-run: without --only every scenario of RCT-4 runs and every failed check is reported."""
        result = suite("--trunk", TRUNK + " --refuse", "--root-contract", "1")
        self.assertEqual(result.returncode, 1, result.stderr)
        lines = result.stdout.splitlines()
        self.assertEqual(lines[0], "FAIL R1 — A plain answer in the background")  # against a Trunk that does nothing
        self.assertEqual([line for line in lines if line.startswith("FAIL ")],
                         [f"FAIL {scenario.id} — {scenario.title}" for scenario in SCENARIOS])
        self.assertEqual(lines[-1], f"0/{len(SCENARIOS)} scenarios passed.")


class Runner(unittest.TestCase):
    def make_home(self, scenario: Scenario) -> ScenarioHome:
        return ScenarioHome.create(scenario.id, FAKE_TRUNK, 1, LAYOUT)

    def test_failure_descriptions_can_print_lone_surrogates_as_valid_utf8(self) -> None:
        text = describe({"text": "\ud83d", "emoji": "😀"})
        self.assertEqual(text.encode("utf-8").decode("utf-8"), text)
        self.assertIn("\\ud83d", text)
        self.assertIn("😀", text)

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

    def test_every_scenario_passing_is_status_0(self) -> None:
        lines: list[str] = []
        status = run_suite([Scenario("T1", "Nothing", (), lambda home: None)], self.make_home, lines.append)
        self.assertEqual((status, lines), (0, ["PASS T1 — Nothing", "1/1 scenarios passed."]))

    def test_only_chooses_scenarios_in_the_order_of_the_registry(self) -> None:
        available = [Scenario("R1", "One", (), lambda home: None), Scenario("R2", "Two", (), lambda home: None)]
        self.assertEqual([s.id for s in select("R2, R1", available)], ["R1", "R2"])
        self.assertEqual([s.id for s in select("R2", available)], ["R2"])
        self.assertEqual(len(select(None, available)), 2)
        with self.assertRaises(ValueError):
            select(" , ", available)


if __name__ == "__main__":
    unittest.main()

# Archived complete imports; restore needed names in their original scope, not at this file tail.
