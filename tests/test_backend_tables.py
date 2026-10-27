"""Backend layout/copy/counter acceptance on a check-owned socket-only server."""

from __future__ import annotations

import contextlib
import shutil
import sys
import tempfile
import time
import unittest
import uuid
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts.backend_tables import counter, rows  # noqa: E402
from scripts.chat_migration_check import invoke, reply  # noqa: E402
from scripts.check_layout import run_layout  # noqa: E402
from scripts.check_migration import Origin, run_migration  # noqa: E402
from scripts.migration_fixtures import CHATS, EXCHANGES, seed  # noqa: E402
from scripts.sql_support import BuildInput, SqlLab, private_server  # noqa: E402


class BackendTables(unittest.TestCase):
    scope: contextlib.ExitStack
    lab: SqlLab

    @classmethod
    def setUpClass(cls) -> None:
        cls.scope = contextlib.ExitStack()
        cls.lab = cls.scope.enter_context(private_server())

    @classmethod
    def tearDownClass(cls) -> None:
        cls.scope.close()

    def setUp(self) -> None:
        temporary = tempfile.TemporaryDirectory(prefix="backend-layout-input-")
        self.addCleanup(temporary.cleanup)
        folder = Path(temporary.name)
        (folder / "layout").mkdir()
        (folder / "roots/sapling").mkdir(parents=True)
        for source, name in [
            ("contract/1/layout.sql", "chat-tables.sql"),
            ("roots/jensen/layout.sql", "root-tables.sql"),
            ("roots/jensen/migrate.sql", "migrate.sql"),
        ]:
            shutil.copy2(ROOT / source, folder / "layout" / name)
        shutil.copy2(ROOT / "roots/sapling/layout.sql", folder / "roots/sapling/layout.sql")
        self.inputs = BuildInput(folder, "jensen", "0", 1, "sapling", ("check", "chat"))

    def pair(self) -> tuple[str, str]:
        source, target = "bk_source_" + uuid.uuid4().hex, "bk_target_" + uuid.uuid4().hex
        for name in (source, target):
            self.lab.server.createdb(name)
            self.lab.run_file(name, self.inputs.file("chat-tables.sql"))
            self.lab.run_file(
                name,
                self.inputs.folder / "roots/sapling/layout.sql"
                if name == source
                else self.inputs.file("root-tables.sql"),
            )
        seed(self.lab.server, source)
        return source, target

    def test_both_layouts_repeat_with_every_table_column_and_sequence_commented(self) -> None:
        """root.backend-layouts"""
        for root in ("sapling", "jensen"):
            shutil.copy2(ROOT / "roots" / root / "layout.sql", self.inputs.folder / "layout/root-tables.sql")
            report = run_layout(self.inputs, self.lab)
            self.assertTrue(report["repeated"])

    def test_whole_copy_is_exact_and_never_reuses_deleted_revisions(self) -> None:
        """root.backend-whole"""
        older = Origin(
            "sapling", 1, self.inputs.file("chat-tables.sql"), self.inputs.folder / "roots/sapling/layout.sql"
        )
        report = run_migration(self.inputs, self.lab, older)
        self.assertEqual((report["unchangedTables"], report["sourceRows"]), (9, 28))
        self.assertEqual(
            report["backendTables"], {"exact": True, "sourceCounterUnchanged": True, "savedNextRevisions": [101, 101]}
        )

    def test_counter_rollback_exhaustion_missing_layout_and_late_failure(self) -> None:
        """root.backend-counter-rollback"""
        source, target = self.pair()
        self.lab.server.execute(target, "SELECT setval('drafts_revision',500,true)")
        before = counter(self.lab.server, target)
        original_rows = rows(self.lab.server, source)
        script = self.inputs.file("migrate.sql")
        original = script.read_text()
        head, tail = original.rsplit("COMMIT;", 1)
        script.write_text(head + "SELECT 1/0;\nCOMMIT;" + tail)
        answer = invoke(self.lab, self.inputs, source, target, "whole")
        self.assertEqual(answer.returncode, 3, answer.stderr)
        self.assertIn("division by zero", answer.stderr)
        self.assertEqual(counter(self.lab.server, target), before)
        self.assertTrue(all(not value for value in rows(self.lab.server, target).values()))
        self.assertEqual(rows(self.lab.server, source), original_rows)
        script.write_text(original)
        self.lab.server.execute(source, "SELECT setval('drafts_revision',9223372036854775807,true)")
        answer = invoke(self.lab, self.inputs, source, target, "whole")
        self.assertEqual(answer.returncode, 3)
        self.assertIn("exhausted", answer.stderr)
        self.assertEqual(counter(self.lab.server, target), before)
        self.assertTrue(all(not value for value in rows(self.lab.server, target).values()))
        self.lab.server.execute(source, "SELECT setval('drafts_revision',100,true); DROP TABLE exchange_notes")
        self.assertEqual(invoke(self.lab, self.inputs, source, target, "whole").returncode, 3)
        self.assertEqual(counter(self.lab.server, target), before)

    def test_target_counter_never_moves_back_and_concurrent_allocator_waits_for_commit(self) -> None:
        """root.backend-counter-lock"""
        source, target = self.pair()
        self.lab.server.execute(target, "SELECT setval('drafts_revision',500,true)")
        script = self.inputs.file("migrate.sql")
        original = script.read_text()
        head, tail = original.rsplit("COMMIT;", 1)
        script.write_text(head + "SELECT pg_sleep(1);\nCOMMIT;" + tail)
        with ThreadPoolExecutor(max_workers=2) as pool:
            migration = pool.submit(invoke, self.lab, self.inputs, source, target, "whole")
            deadline = time.monotonic() + 5
            while not self.lab.server.value(
                target,
                "SELECT to_json(EXISTS(SELECT 1 FROM pg_stat_activity "
                f"WHERE datname='{target}' AND wait_event='PgSleep'))",
            ):
                if migration.done() or time.monotonic() > deadline:
                    self.fail("Counter lock pause never observed")
                time.sleep(0.01)
            allocation = pool.submit(self.lab.server.value, target, "SELECT to_json(nextval('drafts_revision'))")
            time.sleep(0.1)
            self.assertFalse(allocation.done())
            result = migration.result(timeout=5)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(allocation.result(timeout=5), 501)
        self.assertEqual(counter(self.lab.server, source), {"last_value": 100, "log_cnt": 0, "is_called": True})

    def test_reimport_notes_and_local_input_are_preserved_and_pending_send_refuses(self) -> None:
        """root.backend-chat-state"""
        source, target = self.pair()
        self.assertEqual(invoke(self.lab, self.inputs, source, target, "whole").returncode, 0)
        server = self.lab.server
        server.execute(
            target,
            f"UPDATE drafts SET text='local target text' WHERE chat_id='{CHATS[0]}'; "
            f"UPDATE chat_settings SET working_folder='/fictional/local' WHERE chat_id='{CHATS[0]}'; "
            f"UPDATE chat_marks SET ongoing=false WHERE chat_id='{CHATS[0]}'",
        )
        original_source = rows(server, source)
        local = rows(server, target)
        before_counter = counter(server, target)
        reply(invoke(self.lab, self.inputs, source, target, "check"), "check")
        self.assertEqual(rows(server, target), local)
        self.assertEqual(counter(server, target), before_counter)
        result = reply(invoke(self.lab, self.inputs, source, target, "chat", CHATS[0]), "chat")
        self.assertEqual(result["action"], "replaced")
        self.assertEqual(rows(server, target), local)
        server.execute(
            target,
            f"UPDATE drafts SET sent_as='50000000-0000-4000-8000-000000000002',"
            f"sent_request='{{}}' WHERE chat_id='{CHATS[0]}'",
        )
        pending = rows(server, target)
        answer = invoke(self.lab, self.inputs, source, target, "chat", CHATS[0])
        self.assertEqual(answer.returncode, 3)
        self.assertIn("unresolved send", answer.stderr)
        self.assertEqual(rows(server, target), pending)
        server.execute(
            target,
            f"UPDATE drafts SET sent_as=NULL,sent_request=NULL WHERE chat_id='{CHATS[0]}'; "
            f"INSERT INTO exchanges SELECT '{uuid.uuid4()}',chat_id,4,'open',NULL,trunk,build,route,"
            f"small_call_route,working_folder,clock_timestamp(),NULL,NULL FROM exchanges WHERE id='{EXCHANGES[2]}'",
        )
        local = rows(server, target)
        result = reply(invoke(self.lab, self.inputs, source, target, "chat", CHATS[0]), "chat")
        self.assertEqual(result["action"], "copied")
        after = rows(server, target)
        for name in ("drafts", "chat_settings", "chat_marks"):
            self.assertEqual(after[name], local[name])
        notes = server.rows(
            target,
            f"SELECT n.*,e.number FROM exchange_notes n JOIN exchanges e ON e.id=n.exchange_id "
            f"WHERE e.chat_id='{result['resultChat']}'",
        )
        self.assertEqual(len(notes), 1)
        self.assertEqual((notes[0]["number"], notes[0]["kind"]), (1, "ended_stuck"))
        self.assertNotEqual(notes[0]["exchange_id"], EXCHANGES[0])
        self.assertEqual(counter(server, target), before_counter)
        self.assertEqual(rows(server, source), original_source)

    def test_counter_restart_fault_is_detected_by_saved_draft_probe(self) -> None:
        """root.backend-counter-fault"""
        script = self.inputs.file("migrate.sql")
        value = script.read_text()
        old = "(SELECT last_value::numeric+is_called::integer FROM incoming_drafts_revision),"
        self.assertIn(old, value)
        script.write_text(value.replace(old, "1::numeric,"))
        older = Origin(
            "sapling", 1, self.inputs.file("chat-tables.sql"), self.inputs.folder / "roots/sapling/layout.sql"
        )
        with self.assertRaisesRegex(ValueError, "consumed revision"):
            run_migration(self.inputs, self.lab, older)
