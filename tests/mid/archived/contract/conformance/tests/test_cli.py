# Mid-tier source from contract/conformance/tests/test_cli.py; see MID_TIER.md.
# Shared helpers and refusal entry points remain at the original path.

# TEST-TIER-DISABLED-BEGIN contract/conformance/tests/test_cli.py::Cli.test_without_initdb_on_the_search_path_it_ends_with_2_and_names_it
#     def test_without_initdb_on_the_search_path_it_ends_with_2_and_names_it(self) -> None:
#         """cli.programs: with psql, pg_ctl and createdb but no initdb on the search path, the suite ends with 2
#         before any scenario starts and names initdb."""
#         with tempfile.TemporaryDirectory(prefix="rct-path-") as folder:
#             for name in ("psql", "pg_ctl", "createdb"):
#                 found = Path(psql()).parent / name
#                 os.symlink(found, Path(folder) / name)
#             result = suite("--trunk", TRUNK, "--root-contract", "1", path=f"{folder}:/usr/bin:/bin")
#         self.assertEqual(result.returncode, 2, result.stdout + result.stderr)
#         self.assertIn("missing from the search path: initdb.", result.stderr)
#         self.assertEqual(result.stdout, "")
# TEST-TIER-DISABLED-END contract/conformance/tests/test_cli.py::Cli.test_without_initdb_on_the_search_path_it_ends_with_2_and_names_it

# TEST-TIER-DISABLED-BEGIN contract/conformance/tests/test_cli.py::Cli.test_wrong_input_ends_with_2_and_says_what_is_wrong
#     def test_wrong_input_ends_with_2_and_says_what_is_wrong(self) -> None:
#         """cli.input: an unknown option, a missing or doubled option, a Trunk that cannot be run, a version without
#         layout.sql, an unknown scenario, or R16 alone."""
#         cases = {
#             "an unknown option": (["--trunk", TRUNK, "--root-contract", "1", "--fast"], "Unknown option: --fast"),
#             "no --trunk": (["--root-contract", "1"], "Give --trunk."),
#             "no --root-contract": (["--trunk", TRUNK], "Give --root-contract."),
#             "--trunk twice": (["--trunk", TRUNK, "--trunk", TRUNK, "--root-contract", "1"], "only once"),
#             "a Trunk that is not there": (["--trunk", "/nonexistent/arbol-trunk-trivial", "--root-contract", "1"],
#                                           "does not exist or cannot be run"),
#             "a Trunk not on the search path": (["--trunk", "arbol-trunk-nothing", "--root-contract", "1"],
#                                                "is not on the search path"),
#             "version 0": (["--trunk", TRUNK, "--root-contract", "0"], "such as 1, not 0"),
#             "version 2": (["--trunk", TRUNK, "--root-contract", "2"], "version 2 has no layout.sql"),
#             "an unknown scenario": (["--trunk", TRUNK, "--root-contract", "1", "--only", "R1,R99"],
#                                     "Unknown scenario: R99"),
#             "R16 alone": (["--trunk", TRUNK, "--root-contract", "1", "--only", "R16"], "runs after every scenario"),
#         }
#         for name, (args, message) in cases.items():
#             with self.subTest(name):
#                 result = suite(*args)
#                 self.assertEqual(result.returncode, 2, result.stdout + result.stderr)
#                 self.assertIn(message, result.stderr)
#                 self.assertIn("Usage: rct-conformance.py", result.stderr)
# TEST-TIER-DISABLED-END contract/conformance/tests/test_cli.py::Cli.test_wrong_input_ends_with_2_and_says_what_is_wrong

# TEST-TIER-DISABLED-BEGIN contract/conformance/tests/test_cli.py::Cli.test_a_whole_run_lists_every_scenario_and_reports_failures
#     def test_a_whole_run_lists_every_scenario_and_reports_failures(self) -> None:
#         """cli.whole-run: without --only every scenario of RCT-4 runs and every failed check is reported."""
#         result = suite("--trunk", TRUNK + " --refuse", "--root-contract", "1")
#         self.assertEqual(result.returncode, 1, result.stderr)
#         lines = result.stdout.splitlines()
#         self.assertEqual(lines[0], "FAIL R1 — A plain answer in the background")  # against a Trunk that does nothing
#         self.assertEqual([line for line in lines if line.startswith("FAIL ")],
#                          [f"FAIL {scenario.id} — {scenario.title}" for scenario in SCENARIOS])
#         self.assertEqual(lines[-1], f"0/{len(SCENARIOS)} scenarios passed.")
# TEST-TIER-DISABLED-END contract/conformance/tests/test_cli.py::Cli.test_a_whole_run_lists_every_scenario_and_reports_failures

# TEST-TIER-DISABLED-BEGIN contract/conformance/tests/test_cli.py::Runner.test_failure_descriptions_can_print_lone_surrogates_as_valid_utf8
#     def test_failure_descriptions_can_print_lone_surrogates_as_valid_utf8(self) -> None:
#         text = describe({"text": "\ud83d", "emoji": "😀"})
#         self.assertEqual(text.encode("utf-8").decode("utf-8"), text)
#         self.assertIn("\\ud83d", text)
#         self.assertIn("😀", text)
# TEST-TIER-DISABLED-END contract/conformance/tests/test_cli.py::Runner.test_failure_descriptions_can_print_lone_surrogates_as_valid_utf8

# TEST-TIER-DISABLED-BEGIN contract/conformance/tests/test_cli.py::Runner.test_reports_each_scenario_and_runs_r16_after_each
#     def test_reports_each_scenario_and_runs_r16_after_each(self) -> None:
#         """runner.report: PASS for a scenario whose checks and R16 pass, FAIL with what was expected and received for
#         one whose check fails, FAIL naming R16 for one that changes the tables, and the status 1."""
#         def passes(home: ScenarioHome) -> None:
#             started = home.start(extra={"FAKE_TRUNK_MODE": "accept", "FAKE_PSQL": psql()})
#             if not started.answer["accepted"]:
#                 raise Mismatch("not accepted")
#
#         def fails(home: ScenarioHome) -> None:
#             raise Mismatch("The Exchange's state differs.", "completed", "failed")
#
#         def changes_the_tables(home: ScenarioHome) -> None:
#             home.start(extra={"FAKE_TRUNK_MODE": "change-layout", "FAKE_PSQL": psql()})
#
#         homes: list[ScenarioHome] = []
#
#         def make_home(scenario: Scenario) -> ScenarioHome:
#             homes.append(self.make_home(scenario))
#             return homes[-1]
#
#         lines: list[str] = []
#         scenarios = [Scenario("T1", "Passes", (), passes), Scenario("T2", "Fails", (), fails),
#                      Scenario("T3", "Changes the tables", (), changes_the_tables), Scenario("T4", "Not yet", ())]
#         status = run_suite(scenarios, make_home, lines.append)
#         self.assertEqual(status, 1)
#         self.assertEqual(lines[0], "PASS T1 — Passes")
#         self.assertEqual(lines[1:5], ["FAIL T2 — Fails", "  The Exchange's state differs.",
#                                       '  Expected: "completed"', '  Received: "failed"'])
#         self.assertEqual(lines[5], "FAIL T3 — Changes the tables")
#         self.assertIn("R16: the tables are not those layout.sql made", lines[6])
#         self.assertEqual(lines[-3:], ["FAIL T4 — Not yet", "  Not implemented yet.", "1/4 scenarios passed."])
#         self.assertEqual(len(homes), 3)
#         self.assertTrue(all(not home.home.exists() for home in homes))
# TEST-TIER-DISABLED-END contract/conformance/tests/test_cli.py::Runner.test_reports_each_scenario_and_runs_r16_after_each

# TEST-TIER-DISABLED-BEGIN contract/conformance/tests/test_cli.py::Runner.test_every_scenario_passing_is_status_0
#     def test_every_scenario_passing_is_status_0(self) -> None:
#         lines: list[str] = []
#         status = run_suite([Scenario("T1", "Nothing", (), lambda home: None)], self.make_home, lines.append)
#         self.assertEqual((status, lines), (0, ["PASS T1 — Nothing", "1/1 scenarios passed."]))
# TEST-TIER-DISABLED-END contract/conformance/tests/test_cli.py::Runner.test_every_scenario_passing_is_status_0

# TEST-TIER-DISABLED-BEGIN contract/conformance/tests/test_cli.py::Runner.test_only_chooses_scenarios_in_the_order_of_the_registry
#     def test_only_chooses_scenarios_in_the_order_of_the_registry(self) -> None:
#         available = [Scenario("R1", "One", (), lambda home: None), Scenario("R2", "Two", (), lambda home: None)]
#         self.assertEqual([s.id for s in select("R2, R1", available)], ["R1", "R2"])
#         self.assertEqual([s.id for s in select("R2", available)], ["R2"])
#         self.assertEqual(len(select(None, available)), 2)
#         with self.assertRaises(ValueError):
#             select(" , ", available)
# TEST-TIER-DISABLED-END contract/conformance/tests/test_cli.py::Runner.test_only_chooses_scenarios_in_the_order_of_the_registry

# TEST-TIER-IMPORTS-BEGIN contract/conformance/tests/test_cli.py:10
# import tempfile
# TEST-TIER-IMPORTS-END contract/conformance/tests/test_cli.py:10

# TEST-TIER-IMPORTS-BEGIN contract/conformance/tests/test_cli.py:12
# from pathlib import Path
# TEST-TIER-IMPORTS-END contract/conformance/tests/test_cli.py:12

# TEST-TIER-IMPORTS-BEGIN contract/conformance/tests/test_cli.py:15
# from rct_conformance.judge import Mismatch, describe
# TEST-TIER-IMPORTS-END contract/conformance/tests/test_cli.py:15

# TEST-TIER-IMPORTS-BEGIN contract/conformance/tests/test_cli.py:16
# from rct_conformance.registry import SCENARIOS, Scenario, select
# TEST-TIER-IMPORTS-END contract/conformance/tests/test_cli.py:16

# TEST-TIER-IMPORTS-BEGIN contract/conformance/tests/test_cli.py:17
# from rct_conformance.runner import run_suite
# TEST-TIER-IMPORTS-END contract/conformance/tests/test_cli.py:17

# TEST-TIER-IMPORTS-BEGIN contract/conformance/tests/test_cli.py:19
# from .support import CLI, FAKE_TRUNK, LAYOUT, psql
# TEST-TIER-IMPORTS-END contract/conformance/tests/test_cli.py:19

raise RuntimeError("Mid-tier checks require an explicitly requested testing task; see MID_TIER.md.")
