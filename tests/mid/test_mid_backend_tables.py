"""Commented mid-tier selections; see MID_TIER.md before restoring a case."""

# Restore the needed imports and class header only for an explicit testing task.
# import test_backend_tables as _support
# from test_backend_tables import (
#     BackendTables,
#     BuildInput,
#     OperationalBoundary,
#     Path,
#     ROOT,
#     SqlLab,
#     contextlib,
#     private_server,
#     seed,
#     shutil,
#     sys,
#     tempfile,
#     unittest,
#     uuid,
# )


# class OperationalBoundary(_support.OperationalBoundary):
# TEST-TIER-DISABLED-BEGIN tests/test_backend_tables.py::OperationalBoundary.test_default_preview_does_not_open_an_owner_folder_or_start_a_build
#     def test_default_preview_does_not_open_an_owner_folder_or_start_a_build(self) -> None:
#         """sapling.backend-layout-preview"""
#         with tempfile.TemporaryDirectory(prefix="backend-preview-") as home:
#             result = subprocess.run(
#                 [sys.executable, "-I", "-B", str(ROOT / "roots/sapling/drills/drill-backend-layouts.py")],
#                 env={**os.environ, "HOME": home},
#                 capture_output=True,
#                 text=True,
#                 timeout=5,
#             )
#             self.assertEqual(result.returncode, 0, result.stderr)
#             self.assertEqual(
#                 json.loads(result.stdout), {"preflightOnly": True, "roots": ["sapling", "jensen"], "realMessages": 0}
#             )
#             self.assertFalse(list(Path(home).iterdir()))
# TEST-TIER-DISABLED-END tests/test_backend_tables.py::OperationalBoundary.test_default_preview_does_not_open_an_owner_folder_or_start_a_build

# TEST-TIER-DISABLED-BEGIN tests/test_backend_tables.py::OperationalBoundary.test_operational_guard_detects_old_row_schema_and_new_counter_damage
#     def test_operational_guard_detects_old_row_schema_and_new_counter_damage(self) -> None:
#         """sapling.backend-layout-preservation"""
#         sys.path.insert(0, str(ROOT / "roots/sapling/drills"))
#         from backend_layout_drills import BACKEND, preserved
#         from drill_support import DrillError
#
#         before: dict[str, Any] = {
#             "history": {"tables": {"chats": {"encodedRows": ["exact old row"]}}},
#             "schema": {"relations": ["old relation"], "comments": ["old comment"]},
#         }
#         after: dict[str, Any] = {
#             **copy.deepcopy(before),
#             "backend": {"counts": {name: 0 for name in BACKEND}, "counter": {"last_value": 1, "is_called": False}},
#         }
#         preserved(before, after)
#         for fault in ("row", "schema", "counter"):
#             bad = copy.deepcopy(after)
#             if fault == "row":
#                 bad["history"]["tables"]["chats"]["encodedRows"] = ["different"]
#             elif fault == "schema":
#                 bad["schema"]["comments"] = []
#             else:
#                 bad["backend"]["counter"]["is_called"] = True
#             with self.subTest(fault=fault), self.assertRaises(DrillError):
#                 preserved(before, bad)
# TEST-TIER-DISABLED-END tests/test_backend_tables.py::OperationalBoundary.test_operational_guard_detects_old_row_schema_and_new_counter_damage



# class BackendTables(_support.BackendTables):
# TEST-TIER-DISABLED-BEGIN tests/test_backend_tables.py::BackendTables.test_both_layouts_repeat_with_every_table_column_and_sequence_commented
#     def test_both_layouts_repeat_with_every_table_column_and_sequence_commented(self) -> None:
#         """root.backend-layouts"""
#         for root in ("sapling", "jensen"):
#             shutil.copy2(ROOT / "roots" / root / "layout.sql", self.inputs.folder / "layout/root-tables.sql")
#             report = run_layout(self.inputs, self.lab)
#             self.assertTrue(report["repeated"])
# TEST-TIER-DISABLED-END tests/test_backend_tables.py::BackendTables.test_both_layouts_repeat_with_every_table_column_and_sequence_commented

# TEST-TIER-DISABLED-BEGIN tests/test_backend_tables.py::BackendTables.test_whole_copy_is_exact_and_never_reuses_deleted_revisions
#     def test_whole_copy_is_exact_and_never_reuses_deleted_revisions(self) -> None:
#         """root.backend-whole"""
#         older = Origin(
#             "sapling", 1, self.inputs.file("chat-tables.sql"), self.inputs.folder / "roots/sapling/layout.sql"
#         )
#         report = run_migration(self.inputs, self.lab, older)
#         self.assertEqual((report["unchangedTables"], report["sourceRows"]), (12, 28))
#         self.assertEqual(
#             report["backendTables"], {"exact": True, "sourceCounterUnchanged": True, "savedNextRevisions": [101, 101]}
#         )
# TEST-TIER-DISABLED-END tests/test_backend_tables.py::BackendTables.test_whole_copy_is_exact_and_never_reuses_deleted_revisions

# TEST-TIER-DISABLED-BEGIN tests/test_backend_tables.py::BackendTables.test_empty_drafts_keep_consumed_and_not_yet_consumed_counter_states
#     def test_empty_drafts_keep_consumed_and_not_yet_consumed_counter_states(self) -> None:
#         """root.backend-empty-counter"""
#         for called, expected in [(True, 101), (False, 100)]:
#             source, target = self.pair()
#             self.lab.server.execute(
#                 source,
#                 "DELETE FROM drafts; SELECT setval('drafts_revision',100," + ("true" if called else "false") + ")",
#             )
#             before = counter(self.lab.server, source)
#             answer = invoke(self.lab, self.inputs, source, target, "whole")
#             self.assertEqual(answer.returncode, 0, answer.stderr)
#             self.assertEqual(self.lab.server.value(target, "SELECT to_json(nextval('drafts_revision'))"), expected)
#             self.assertEqual(counter(self.lab.server, source), before)
# TEST-TIER-DISABLED-END tests/test_backend_tables.py::BackendTables.test_empty_drafts_keep_consumed_and_not_yet_consumed_counter_states

# TEST-TIER-DISABLED-BEGIN tests/test_backend_tables.py::BackendTables.test_counter_rollback_exhaustion_missing_layout_and_late_failure
#     def test_counter_rollback_exhaustion_missing_layout_and_late_failure(self) -> None:
#         """root.backend-counter-rollback"""
#         source, target = self.pair()
#         self.lab.server.execute(target, "SELECT setval('drafts_revision',500,true)")
#         before = counter(self.lab.server, target)
#         original_rows = rows(self.lab.server, source)
#         script = self.inputs.file("migrate.sql")
#         original = script.read_text()
#         head, tail = original.rsplit("COMMIT;", 1)
#         script.write_text(head + "SELECT 1/0;\nCOMMIT;" + tail)
#         answer = invoke(self.lab, self.inputs, source, target, "whole")
#         self.assertEqual(answer.returncode, 3, answer.stderr)
#         self.assertIn("division by zero", answer.stderr)
#         self.assertEqual(counter(self.lab.server, target), before)
#         self.assertTrue(all(not value for value in rows(self.lab.server, target).values()))
#         self.assertEqual(rows(self.lab.server, source), original_rows)
#         script.write_text(original)
#         self.lab.server.execute(source, "SELECT setval('drafts_revision',9223372036854775807,true)")
#         answer = invoke(self.lab, self.inputs, source, target, "whole")
#         self.assertEqual(answer.returncode, 3)
#         self.assertIn("exhausted", answer.stderr)
#         self.assertEqual(counter(self.lab.server, target), before)
#         self.assertTrue(all(not value for value in rows(self.lab.server, target).values()))
#         self.lab.server.execute(source, "SELECT setval('drafts_revision',100,true); DROP TABLE exchange_notes")
#         self.assertEqual(invoke(self.lab, self.inputs, source, target, "whole").returncode, 3)
#         self.assertEqual(counter(self.lab.server, target), before)
# TEST-TIER-DISABLED-END tests/test_backend_tables.py::BackendTables.test_counter_rollback_exhaustion_missing_layout_and_late_failure

# TEST-TIER-DISABLED-BEGIN tests/test_backend_tables.py::BackendTables.test_target_counter_never_moves_back_and_concurrent_allocator_waits_for_commit
#     def test_target_counter_never_moves_back_and_concurrent_allocator_waits_for_commit(self) -> None:
#         """root.backend-counter-lock"""
#         source, target = self.pair()
#         self.lab.server.execute(target, "SELECT setval('drafts_revision',500,true)")
#         script = self.inputs.file("migrate.sql")
#         original = script.read_text()
#         head, tail = original.rsplit("COMMIT;", 1)
#         script.write_text(head + "SELECT pg_sleep(1);\nCOMMIT;" + tail)
#         with ThreadPoolExecutor(max_workers=2) as pool:
#             migration = pool.submit(invoke, self.lab, self.inputs, source, target, "whole")
#             deadline = time.monotonic() + 5
#             while not self.lab.server.value(
#                 target,
#                 "SELECT to_json(EXISTS(SELECT 1 FROM pg_stat_activity "
#                 f"WHERE datname='{target}' AND wait_event='PgSleep'))",
#             ):
#                 if migration.done() or time.monotonic() > deadline:
#                     self.fail("Counter lock pause never observed")
#                 time.sleep(0.01)
#             allocation = pool.submit(self.lab.server.value, target, "SELECT to_json(nextval('drafts_revision'))")
#             time.sleep(0.1)
#             self.assertFalse(allocation.done())
#             result = migration.result(timeout=5)
#             self.assertEqual(result.returncode, 0, result.stderr)
#             self.assertEqual(allocation.result(timeout=5), 501)
#         self.assertEqual(counter(self.lab.server, source), {"last_value": 100, "log_cnt": 0, "is_called": True})
# TEST-TIER-DISABLED-END tests/test_backend_tables.py::BackendTables.test_target_counter_never_moves_back_and_concurrent_allocator_waits_for_commit

# TEST-TIER-DISABLED-BEGIN tests/test_backend_tables.py::BackendTables.test_reimport_notes_and_local_input_are_preserved_and_pending_send_refuses
#     def test_reimport_notes_and_local_input_are_preserved_and_pending_send_refuses(self) -> None:
#         """root.backend-chat-state"""
#         source, target = self.pair()
#         self.assertEqual(invoke(self.lab, self.inputs, source, target, "whole").returncode, 0)
#         server = self.lab.server
#         server.execute(
#             target,
#             f"UPDATE drafts SET text='local target text' WHERE chat_id='{CHATS[0]}'; "
#             f"UPDATE chat_settings SET working_folder='/fictional/local' WHERE chat_id='{CHATS[0]}'; "
#             f"UPDATE chat_marks SET ongoing=false WHERE chat_id='{CHATS[0]}'",
#         )
#         original_source = rows(server, source)
#         local = rows(server, target)
#         before_counter = counter(server, target)
#         reply(invoke(self.lab, self.inputs, source, target, "check"), "check")
#         self.assertEqual(rows(server, target), local)
#         self.assertEqual(counter(server, target), before_counter)
#         result = reply(invoke(self.lab, self.inputs, source, target, "chat", CHATS[0]), "chat")
#         self.assertEqual(result["action"], "replaced")
#         self.assertEqual(rows(server, target), local)
#         server.execute(
#             target,
#             f"UPDATE drafts SET sent_as='50000000-0000-4000-8000-000000000002',"
#             f"sent_request='{{}}' WHERE chat_id='{CHATS[0]}'",
#         )
#         pending = rows(server, target)
#         answer = invoke(self.lab, self.inputs, source, target, "chat", CHATS[0])
#         self.assertEqual(answer.returncode, 3)
#         self.assertIn("unresolved send", answer.stderr)
#         self.assertEqual(rows(server, target), pending)
#         server.execute(
#             target,
#             f"UPDATE drafts SET sent_as=NULL,sent_request=NULL WHERE chat_id='{CHATS[0]}'; "
#             f"INSERT INTO exchanges SELECT '{uuid.uuid4()}',chat_id,4,'open',NULL,trunk,build,route,"
#             f"small_call_route,working_folder,clock_timestamp(),NULL,NULL FROM exchanges WHERE id='{EXCHANGES[2]}'",
#         )
#         local = rows(server, target)
#         result = reply(invoke(self.lab, self.inputs, source, target, "chat", CHATS[0]), "chat")
#         self.assertEqual(result["action"], "copied")
#         after = rows(server, target)
#         for name in ("drafts", "chat_settings", "chat_marks"):
#             self.assertEqual(after[name], local[name])
#         notes = server.rows(
#             target,
#             f"SELECT n.*,e.number FROM exchange_notes n JOIN exchanges e ON e.id=n.exchange_id "
#             f"WHERE e.chat_id='{result['resultChat']}'",
#         )
#         self.assertEqual(len(notes), 1)
#         self.assertEqual((notes[0]["number"], notes[0]["kind"]), (1, "ended_stuck"))
#         self.assertNotEqual(notes[0]["exchange_id"], EXCHANGES[0])
#         self.assertEqual(counter(server, target), before_counter)
#         self.assertEqual(rows(server, source), original_source)
# TEST-TIER-DISABLED-END tests/test_backend_tables.py::BackendTables.test_reimport_notes_and_local_input_are_preserved_and_pending_send_refuses

# TEST-TIER-DISABLED-BEGIN tests/test_backend_tables.py::BackendTables.test_counter_restart_fault_is_detected_by_saved_draft_probe
#     def test_counter_restart_fault_is_detected_by_saved_draft_probe(self) -> None:
#         """root.backend-counter-fault"""
#         script = self.inputs.file("migrate.sql")
#         value = script.read_text()
#         old = "(SELECT last_value::numeric+is_called::integer FROM incoming_drafts_revision),"
#         self.assertIn(old, value)
#         script.write_text(value.replace(old, "1::numeric,"))
#         older = Origin(
#             "sapling", 1, self.inputs.file("chat-tables.sql"), self.inputs.folder / "roots/sapling/layout.sql"
#         )
#         with self.assertRaisesRegex(ValueError, "consumed revision"):
#             run_migration(self.inputs, self.lab, older)
# TEST-TIER-DISABLED-END tests/test_backend_tables.py::BackendTables.test_counter_restart_fault_is_detected_by_saved_draft_probe


# Original deferred imports (restore at the required scope, never blindly at the tail).
# TEST-TIER-IMPORTS-BEGIN tests/test_backend_tables.py:6
# import copy
# TEST-TIER-IMPORTS-END tests/test_backend_tables.py:6

# TEST-TIER-IMPORTS-BEGIN tests/test_backend_tables.py:7
# import json
# TEST-TIER-IMPORTS-END tests/test_backend_tables.py:7

# TEST-TIER-IMPORTS-BEGIN tests/test_backend_tables.py:8
# import os
# TEST-TIER-IMPORTS-END tests/test_backend_tables.py:8

# TEST-TIER-IMPORTS-BEGIN tests/test_backend_tables.py:10
# import subprocess
# TEST-TIER-IMPORTS-END tests/test_backend_tables.py:10

# TEST-TIER-IMPORTS-BEGIN tests/test_backend_tables.py:13
# import time
# TEST-TIER-IMPORTS-END tests/test_backend_tables.py:13

# TEST-TIER-IMPORTS-BEGIN tests/test_backend_tables.py:16
# from concurrent.futures import ThreadPoolExecutor
# TEST-TIER-IMPORTS-END tests/test_backend_tables.py:16

# TEST-TIER-IMPORTS-BEGIN tests/test_backend_tables.py:18
# from typing import Any
# TEST-TIER-IMPORTS-END tests/test_backend_tables.py:18

# TEST-TIER-IMPORTS-BEGIN tests/test_backend_tables.py:22
# from scripts.backend_tables import counter, rows  # noqa: E402
# TEST-TIER-IMPORTS-END tests/test_backend_tables.py:22

# TEST-TIER-IMPORTS-BEGIN tests/test_backend_tables.py:23
# from scripts.chat_migration_check import invoke, reply  # noqa: E402
# TEST-TIER-IMPORTS-END tests/test_backend_tables.py:23

# TEST-TIER-IMPORTS-BEGIN tests/test_backend_tables.py:24
# from scripts.check_layout import run_layout  # noqa: E402
# TEST-TIER-IMPORTS-END tests/test_backend_tables.py:24

# TEST-TIER-IMPORTS-BEGIN tests/test_backend_tables.py:25
# from scripts.check_migration import Origin, run_migration  # noqa: E402
# TEST-TIER-IMPORTS-END tests/test_backend_tables.py:25

# TEST-TIER-IMPORTS-BEGIN tests/test_backend_tables.py:26
# from scripts.migration_fixtures import CHATS, EXCHANGES, seed  # noqa: E402
# TEST-TIER-IMPORTS-END tests/test_backend_tables.py:26

raise RuntimeError("Mid-tier tests require an explicitly requested testing task; see MID_TIER.md.")
