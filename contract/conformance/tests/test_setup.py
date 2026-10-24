"""A scenario's home (RCT-4.1, 4.2): its setup makes the home, the server, the Root record and the database; the
starter starts the Trunk Build's program as `arbol-root` does, with a minimal environment; R16 judges the tables after
the scenario; and closing the home leaves nothing behind. A fake Trunk (fake_trunk.py) stands for a Trunk Build."""

from __future__ import annotations

import json
import os
import stat
import subprocess
import time
import unittest
import uuid
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Any
from unittest import mock
from urllib.parse import unquote

from rct_conformance.home import DATABASE, ROUTE, ScenarioHome
from rct_conformance.judge import Mismatch, wait_until
from rct_conformance.postgres import PORT, SOCKET_PATH_LIMIT

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
    def test_setup_makes_the_home_the_server_the_root_record_and_the_database(self) -> None:
        """setup.makes: a temporary home; a server of its own made with initdb in it, trusting the role rct and
        listening only on a socket in a short folder under /tmp; the Root record with the version under test and
        arbol_rct; an empty exchanges/ of the mode 0700; the database made from layout.sql; database.json with the
        socket's address."""
        home = self.home()
        self.assertTrue(home.home.is_dir())
        self.assertEqual(home.server.data, home.home / "postgres")
        self.assertTrue(home.server.running())
        record = json.loads((home.root_folder / "root.json").read_text())
        self.assertEqual(home.root_folder, home.home / "Library/Application Support/Arbol/roots/rct")
        self.assertEqual((record["root"], record["rootContract"], record["database"]), ("rct", 1, "arbol_rct"))
        self.assertEqual(os.listdir(home.exchanges_folder), [])
        self.assertEqual(stat.S_IMODE(os.stat(home.exchanges_folder).st_mode), 0o700)
        address = json.loads((home.home / ".arbol/database.json").read_text())
        self.assertEqual(list(address), ["address"])
        self.assertRegex(address["address"], r"^postgresql://rct@%2Ftmp%2Frct-[a-z0-9_]+$")
        folder = Path(unquote(address["address"].split("@", 1)[1]))
        self.assertEqual(folder.parent, Path("/tmp"))
        self.assertLessEqual(len(os.fsencode(folder / f".s.PGSQL.{PORT}")), SOCKET_PATH_LIMIT)
        self.assertTrue((folder / f".s.PGSQL.{PORT}").is_socket())
        settings = home.rows("SELECT current_setting('listen_addresses') AS listen, current_user AS role,"
                             " current_database() AS database")
        self.assertEqual(settings, [{"listen": "", "role": "rct", "database": DATABASE}])
        tables = home.rows("SELECT table_name AS name FROM information_schema.tables WHERE table_schema = 'public'"
                           " ORDER BY 1")
        self.assertEqual([row["name"] for row in tables], ["chats", "exchanges", "messages", "runs", "tool_calls"])
        hba = (home.server.data / "pg_hba.conf").read_text()
        self.assertRegex(hba, r"(?m)^local\s+all\s+all\s+trust")

    def test_closing_leaves_nothing_behind(self) -> None:
        """setup.leaves-nothing: closing ends the Trunk's process group and the stand-in's children, stops the server
        and removes its socket folder and the home."""
        home = ScenarioHome.create("T2", FAKE_TRUNK, 1, LAYOUT)
        try:
            started = home.start(extra={"FAKE_TRUNK_MODE": "linger"})
            self.assertTrue(started.answer["accepted"])
            child = subprocess.Popen(["/bin/sleep", "3600"], start_new_session=True)
            (home.standin / "children.jsonl").write_text(json.dumps({"pid": child.pid}) + "\n")
            postmaster = home.server.postmaster_pid()
            assert postmaster is not None
            socket_folder = home.server.socket_folder
        except BaseException:
            home.close()
            raise
        home.close()
        child.wait(10)
        self.assertFalse(home.home.exists())
        self.assertFalse(socket_folder.exists())
        self.assertFalse(alive(postmaster))
        self.assertFalse(group_alive(started.process.pid))
        self.assertIsNotNone(child.returncode)

    def test_the_starter_starts_run_detach_as_arbol_root_does(self) -> None:
        """setup.starter: `--root rct run --detach --exchange <id> --request <file>`, in a process group and session
        of its own, with standard input from /dev/null, from the home's work folder; the request file names the
        Driver, the Subscription and the model, and is removed once the one line is read."""
        home = self.home()
        exchange = str(uuid.uuid4())
        started = home.start("What does build.sh do?", exchange=exchange)
        report = self.report(home)
        arguments = report["arguments"]
        self.assertEqual(arguments[:6], ["--root", "rct", "run", "--detach", "--exchange", exchange])
        self.assertEqual(arguments[6], "--request")
        self.assertEqual(len(arguments), 8)
        self.assertFalse(Path(arguments[7]).exists())
        self.assertEqual(report["request"], {"route": ROUTE, "message": "What does build.sh do?"})
        self.assertEqual(set(ROUTE), {"driver", "subscription", "model"})
        self.assertEqual(report["sid"], report["pid"])
        self.assertEqual(report["pgid"], report["pid"])
        self.assertEqual(report["pid"], started.process.pid)
        self.assertTrue(report["stdinIsDevNull"])
        self.assertEqual(os.path.realpath(report["workingDirectory"]), os.path.realpath(home.work))
        self.assertEqual(started.answer["exchange"], exchange)
        self.assertIn(exchange, home.exchanges)
        self.assertLess(started.seconds, 15)

    def test_the_starter_names_another_root_when_a_scenario_asks(self) -> None:
        """setup.starter: a scenario may start the Trunk for another Root identifier, such as `../rct`."""
        home = self.home()
        home.start("What does build.sh do?", root="../rct")
        self.assertEqual(self.report(home)["arguments"][:3], ["--root", "../rct", "run"])

    def test_naming_a_part_takes_back_the_release_of_a_held_run(self) -> None:
        home = self.home()
        home.part("busy")
        home.release()
        self.assertTrue((home.standin / "release").exists())
        home.part("next")
        self.assertFalse((home.standin / "release").exists())

    def test_the_trunk_gets_only_home_path_lang_and_the_tests_own_variables(self) -> None:
        """setup.environment: HOME is the home, the stand-in comes first on PATH under both launcher names, and
        ARBOL_TEST_TIME_SCALE is 10 unless a scenario says otherwise; ARBOL_TEST_HANG=1 where a scenario asks."""
        home = self.home()
        home.start()
        environment = self.report(home)["environment"]
        self.assertEqual(set(environment) - {"__CF_USER_TEXT_ENCODING"},
                         {"HOME", "PATH", "LANG", "ARBOL_TEST_TIME_SCALE"})
        self.assertEqual(environment["HOME"], str(home.home))
        self.assertEqual(environment["ARBOL_TEST_TIME_SCALE"], "10")
        self.assertEqual(environment["PATH"].split(":")[0], str(home.standin / "bin"))
        self.assertEqual(self.report(home)["driver"], str(home.standin / "bin" / "arbol-claude-driver"))
        self.assertEqual(self.report(home)["codexDriver"], str(home.standin / "bin" / "arbol-codex-driver"))
        home.start(scale=1, hang=True)
        environment = self.report(home)["environment"]
        self.assertEqual((environment["ARBOL_TEST_TIME_SCALE"], environment["ARBOL_TEST_HANG"]), ("1", "1"))

    def test_the_owners_postgresql_settings_reach_neither_the_suite_nor_the_trunk(self) -> None:
        """setup.isolated: PG… variables of the owner's shell change nothing, and the Trunk gets none of them."""
        owner = {"PGHOST": "127.0.0.1", "PGPORT": "5432", "PGUSER": "postgres", "PGDATABASE": "postgres",
                 "PGPASSWORD": "not-a-password", "PGSERVICE": "nothing", "PSQLRC": "/nonexistent"}
        with mock.patch.dict(os.environ, owner):
            home = self.home()
            self.assertEqual(home.rows("SELECT current_database() AS d"), [{"d": DATABASE}])
            home.start()
        self.assertFalse(set(self.report(home)["environment"]) & set(owner))

    def test_a_command_runs_to_its_end(self) -> None:
        """setup.command: a command such as settle runs in the foreground, and its exit status and lines are read."""
        home = self.home()
        exchange = str(uuid.uuid4())
        completed = home.run(["settle", exchange])
        self.assertEqual(completed.status, 0)
        self.assertEqual(completed.output, [{"exchange": exchange, "settled": "none"}])

    def test_the_stand_in_is_what_the_trunk_starts_as_its_driver(self) -> None:
        """setup.stand-in: a Trunk that starts arbol-claude-driver from its search path starts the stand-in, which
        plays the scenario's script and records the start in received.jsonl."""
        home = self.home("selftest")
        home.part("plain")
        started = home.start(extra=self.mode("standin"))
        self.assertTrue(started.answer["accepted"])
        record = wait_until(home.received, 10, "the stand-in's record")[0]
        self.assertEqual((record["scenario"], record["part"], record["launcher"]),
                         ("selftest", "plain", "arbol-claude-driver"))
        self.assertEqual(record["arguments"][:2], ["run", "--control"])
        events = [json.loads(line) for line in (home.home / "fake-standin.jsonl").read_text().splitlines()]
        self.assertEqual(events[-1]["type"], "finished")
        self.assertEqual(events[-1]["outcome"], "completed")


class Starts(HomeTest):
    def test_a_foreground_start_keeps_the_pipe_and_the_lines_after_acceptance(self) -> None:
        home = self.home()
        started = home.start(detach=False, extra=self.mode("foreground"))
        assert started.process.stdout is not None
        self.assertFalse(started.process.stdout.closed)
        output, _ = started.process.communicate(timeout=10)
        self.assertEqual(json.loads(output)["event"]["text"], "kept after acceptance")
        report = json.loads((home.home / "fake-trunk.json").read_text())
        self.assertNotIn("--detach", report["arguments"])

    def test_starts_from_several_threads_at_once_each_get_files_of_their_own(self) -> None:
        """setup.threads: request files made from several threads at once never share a name."""
        home = self.home()
        with ThreadPoolExecutor(8) as pool:
            files = list(pool.map(lambda _i: home.request_file({}), range(200)))
        self.assertEqual(len(set(files)), 200)

    def test_meanwhile_runs_once_the_trunk_is_started_and_before_its_line_is_read(self) -> None:
        """setup.meanwhile: start() runs its meanwhile with the Trunk's process started and its line not read yet."""
        home = self.home()
        seen: list[bool] = []
        started = home.start(extra=self.mode("report"), meanwhile=lambda: seen.append(bool(home.processes)))
        self.assertEqual(seen, [True])
        self.assertTrue(started.answer["accepted"])

    def test_held_acceptances_wait_until_the_hold_is_released_and_rows_can_be_read_meanwhile(self) -> None:
        """setup.hold: while acceptances are held, a Trunk's insert into chats waits and the tables can be read; once
        the hold is released, the acceptance goes on."""
        home = self.home()
        counted: list[Any] = []
        with home.acceptances_held() as held:
            def meanwhile() -> None:
                time.sleep(0.5)
                counted.append(home.rows("SELECT count(*) AS n FROM chats")[0]["n"])
                held.release()

            started = home.start(extra=self.mode("accept"), meanwhile=meanwhile)
        self.assertEqual(counted, [0])
        self.assertGreater(started.seconds, 0.5)
        self.assertTrue(started.answer["accepted"])
        self.assertEqual(home.rows("SELECT count(*) AS n FROM chats"), [{"n": 1}])


class R16(HomeTest):
    def test_passes_when_every_row_belongs_to_an_exchange_the_scenario_ran(self) -> None:
        """r16.passes: the rows of the Exchanges the scenario's acceptance lines named, and an unchanged layout."""
        home = self.home()
        started = home.start(extra=self.mode("accept"))
        self.assertTrue(started.answer["accepted"])
        self.assertEqual(len(home.rows("SELECT id FROM exchanges")), 1)
        home.no_table_changed()

    def test_finds_a_table_a_column_and_an_index_that_layout_sql_did_not_make(self) -> None:
        """r16.layout: a table, a column and an index added by the Trunk are each named."""
        home = self.home()
        home.start(extra=self.mode("change-layout"))
        with self.assertRaises(Mismatch) as failure:
            home.no_table_changed()
        message = str(failure.exception)
        self.assertIn("added relations: public.extra (kind r)", message)
        self.assertIn("added columns: public.chats.extra text", message)
        self.assertIn("added indexes: CREATE INDEX messages_by_text", message)

    def test_finds_rows_of_an_exchange_the_scenario_did_not_run(self) -> None:
        """r16.rows: a chat and an Exchange that no acceptance line named are found."""
        home = self.home()
        home.start(extra=self.mode("foreign-row"))
        with self.assertRaises(Mismatch) as failure:
            home.no_table_changed()
        message = str(failure.exception)
        self.assertRegex(message, r"exchanges: [0-9a-f-]{36}")
        self.assertRegex(message, r"messages: rows of Exchange [0-9a-f-]{36}")
        self.assertRegex(message, r"chats: [0-9a-f-]{36}")

    def test_starts_the_server_again_when_a_scenario_left_it_stopped(self) -> None:
        """r16.server: a scenario that stops the server, such as R12, still gets R16."""
        home = self.home()
        home.server.stop()
        home.no_table_changed()
        self.assertTrue(home.server.running())


class Readers(HomeTest):
    def test_readers_skip_dot_folders_and_an_unfinished_last_line(self) -> None:
        """setup.readers: a folder whose name starts with a dot is not listed, and the last line of events.jsonl
        without its newline is not read."""
        home = self.home()
        exchange = str(uuid.uuid4())
        folder = home.exchanges_folder / exchange
        folder.mkdir()
        (home.exchanges_folder / f".{uuid.uuid4()}.new").mkdir()
        (folder / "record.json").write_text(json.dumps({"exchange": exchange}))
        (folder / "events.jsonl").write_text('{"n":1,"event":{}}\n{"n":2,"end":{"state":"comp')
        (folder / "control").write_text("")
        self.assertEqual(home.folders(), [exchange])
        self.assertEqual(len(home.folders(hidden=True)), 2)
        self.assertEqual(home.record(exchange), {"exchange": exchange})
        self.assertEqual(home.events(exchange), [{"n": 1, "event": {}}])
        home.control(exchange, {"type": "stop"})
        self.assertEqual((folder / "control").read_text(), '{"type":"stop"}\n')
        self.assertIsNone(home.record(str(uuid.uuid4())))

    def test_wait_until_gives_the_first_value_or_fails(self) -> None:
        began = time.monotonic()
        self.assertEqual(wait_until(lambda: time.monotonic() - began > 0.1 and "done", 5, "a value"), "done")
        with self.assertRaises(Mismatch):
            wait_until(lambda: None, 0.1, "nothing")


if __name__ == "__main__":
    unittest.main()
