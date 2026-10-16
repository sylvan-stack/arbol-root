"""The stand-in Driver (RCT-4, "The stand-in Driver"), started through its launchers as a Trunk starts a Driver: it
plays a script, writes events as a Driver does, stops a run as a Driver does, and records each start."""

from __future__ import annotations

import json
import os
import signal
import subprocess
import sys
import tempfile
import time
import unittest
from pathlib import Path
from typing import IO, Any

from rct_conformance.home import SYSTEM_PATH, write_launchers
from rct_conformance.judge import json_lines, wait_until

from .test_setup import group_alive


class StandIn(unittest.TestCase):
    def setUp(self) -> None:
        folder = tempfile.TemporaryDirectory(prefix="rct-standin-")
        self.addCleanup(folder.cleanup)
        self.home = Path(folder.name)
        (self.home / "standin" / "bin").mkdir(parents=True)
        write_launchers(self.home / "standin" / "bin", os.path.realpath(sys.executable))
        self.processes: list[subprocess.Popen[bytes]] = []
        self.addCleanup(self.end_processes)

    def end_processes(self) -> None:
        for process in self.processes:
            if process.poll() is None:
                process.kill()
            process.wait()
            for stream in (process.stdin, process.stdout):
                if stream is not None:
                    stream.close()

    def scenario(self, name: str) -> None:
        (self.home / "standin" / "scenario").write_text(name + "\n")

    def start(self, args: list[str], *, launcher: str = "arbol-claude-driver") -> subprocess.Popen[bytes]:
        env = {"HOME": str(self.home), "PATH": f"{self.home / 'standin' / 'bin'}:{SYSTEM_PATH}", "LANG": "C",
               "ARBOL_TEST_TIME_SCALE": "10"}
        process = subprocess.Popen([launcher, *args], env=env, cwd=self.home, stdin=subprocess.PIPE,
                                   stdout=subprocess.PIPE)
        self.processes.append(process)
        return process

    def request(self, **fields: Any) -> str:
        body = {"runId": "run-1", "tools": "all", "input": {"role": "user", "text": "What does build.sh do?"},
                "workingDirectory": str(self.home), "labels": {"exchange": "7f3a"}, **fields}
        file = self.home / f"request-{len(self.processes)}.json"
        file.write_text(json.dumps(body))
        return str(file)

    @staticmethod
    def next_event(stream: IO[bytes] | None) -> Any:
        assert stream is not None
        return json.loads(stream.readline())

    def events_until(self, process: subprocess.Popen[bytes], kind: str) -> list[Any]:
        events = []
        while True:
            event = self.next_event(process.stdout)
            events.append(event)
            if event["type"] == kind:
                return events

    def play(self, args: list[str]) -> tuple[int, list[Any]]:
        """A run with a control input that stays open until its finished event, as a Trunk keeps it."""
        process = self.start(args)
        events = self.events_until(process, "finished")
        assert process.stdin is not None
        process.stdin.close()
        return process.wait(15), events

    def received(self) -> list[Any]:
        return json_lines(self.home / "standin" / "received.jsonl")

    def test_plays_a_script_and_records_what_it_received(self) -> None:
        """standin.plays: the script of the scenario named in <home>/standin/scenario, as a Driver writes events:
        one runId, seq from 1 without gaps, the labels on every event, text before the tool call that follows it, and
        finished last; the record holds the arguments, the request as read, the control lines, the lines it wrote and
        the signals."""
        self.scenario("selftest plain")
        file = self.request()
        status, events = self.play(["run", "--control", "--request", file])
        self.assertEqual(status, 0)
        self.assertEqual([event["seq"] for event in events], list(range(1, len(events) + 1)))
        self.assertEqual({event["runId"] for event in events}, {"run-1"})
        self.assertTrue(all(event["labels"] == {"exchange": "7f3a"} for event in events))
        self.assertEqual([event["type"] for event in events],
                         ["started", "text_delta", "text_delta", "text", "tool_started", "tool_output_delta",
                          "tool_finished", "text", "usage", "finished"])
        self.assertEqual(events[0]["continuity"], "fresh")
        self.assertEqual(events[-1]["outcome"], "completed")
        self.assertEqual(events[-1]["usage"]["inputTokens"], 100)
        self.assertRegex(events[0]["at"], r"^\d{4}-\d\d-\d\dT\d\d:\d\d:\d\d\.\d{3}Z$")
        record = self.received()
        self.assertEqual(len(record), 1)
        written = record[0].pop("events")
        self.assertEqual([json.loads(line) for line in written], events)
        self.assertEqual(record[0], {"scenario": "selftest", "part": "plain", "launcher": "arbol-claude-driver",
                                     "arguments": ["run", "--control", "--request", file],
                                     "request": json.loads(Path(file).read_text()), "control": [], "signals": [],
                                     "workingDirectory": os.path.realpath(self.home)})

    def test_a_stop_line_stops_the_run_as_a_driver_does(self) -> None:
        """standin.stop: a stop line on the control input finishes the open tool call as interrupted and the run as
        cancelled, with the exit status 2, and the line is recorded unchanged."""
        self.scenario("selftest stop")
        process = self.start(["run", "--control", "--request", self.request()])
        self.events_until(process, "tool_started")
        assert process.stdin is not None
        process.stdin.write(b'{"type":"stop"}\n')
        process.stdin.flush()
        events = self.events_until(process, "finished")
        self.assertEqual(process.wait(15), 2)
        self.assertEqual(events[0]["type"], "tool_finished")
        self.assertEqual((events[0]["ok"], events[0]["interrupted"]), (False, True))
        self.assertEqual(events[-1]["outcome"], "cancelled")
        self.assertEqual(self.received()[0]["control"], [{"type": "stop"}])

    def test_sigterm_stops_the_run_and_ends_its_child(self) -> None:
        """standin.sigterm: a child started in a process group of its own is ended when the stand-in gets SIGTERM,
        and the signal is recorded."""
        self.scenario("selftest child")
        process = self.start(["run", "--control", "--request", self.request()])
        self.events_until(process, "tool_started")
        children = wait_until(lambda: json_lines(self.home / "standin" / "children.jsonl"), 10, "the child")
        child = int(children[0]["pid"])
        self.assertTrue(group_alive(child))
        self.assertNotEqual(os.getpgid(child), os.getpgid(process.pid))
        process.send_signal(signal.SIGTERM)
        events = self.events_until(process, "finished")
        self.assertEqual(process.wait(15), 2)
        self.assertEqual(events[-1]["outcome"], "cancelled")
        wait_until(lambda: not group_alive(child), 5, "the child's group to end")
        self.assertEqual(self.received()[0]["signals"], ["SIGTERM"])

    def test_the_end_of_the_control_input_stops_the_run(self) -> None:
        """standin.eof: the run's control input ending stops the run, as DRV-2.26 says."""
        self.scenario("selftest stop")
        process = self.start(["run", "--control", "--request", self.request()])
        self.events_until(process, "tool_started")
        assert process.stdin is not None
        process.stdin.close()
        self.assertEqual(self.events_until(process, "finished")[-1]["outcome"], "cancelled")
        self.assertEqual(process.wait(15), 2)

    def test_an_answer_reaches_the_open_question(self) -> None:
        """standin.answer: an answer line for the open question closes it, and the run goes on to its end."""
        self.scenario("selftest ask")
        process = self.start(["run", "--control", "--request", self.request()])
        opened = self.events_until(process, "ask_opened")[-1]
        answer = {"type": "answer", "askId": opened["askId"], "answer": {"type": "answers",
                                                                         "answers": {"branch": ["main"]}}}
        assert process.stdin is not None
        process.stdin.write((json.dumps(answer) + "\n").encode())
        process.stdin.write(b'{"type":"answer","askId":"ask_404","answer":{"type":"decline"}}\n')
        process.stdin.flush()
        events = self.events_until(process, "finished")
        self.assertEqual(process.wait(15), 0)
        refused = [event for event in events if event["type"] == "control_refused"]
        self.assertEqual([(event["askId"], event["error"]["code"]) for event in refused], [("ask_404", "not_found")])
        events = [event for event in events if event["type"] != "control_refused"]
        self.assertEqual([event["type"] for event in events[:2]], ["ask_closed", "tool_finished"])
        self.assertEqual(events[0]["reason"], "answered")
        self.assertEqual(events[1]["result"], answer["answer"])
        self.assertEqual(self.received()[0]["control"][0], answer)

    def test_a_run_without_tools_and_chat_session_is_a_title(self) -> None:
        """standin.title: a run with "tools": "none" and no chat session gets one text, "Stand-in title"."""
        self.scenario("R19 route")
        process = self.start(["run", "--model", "small-model", "Make a title for: What does build.sh do?"])
        output, _ = process.communicate(timeout=30)
        events = [json.loads(line) for line in output.decode().splitlines()]
        self.assertEqual(process.returncode, 0)
        self.assertEqual([event["text"] for event in events if event["type"] == "text"], ["Stand-in title"])
        self.assertEqual(events[-1]["outcome"], "completed")
        self.assertEqual(self.received()[0]["request"]["tools"], "none")

    def test_a_scenario_without_a_script_fails_the_run(self) -> None:
        """standin.no-script: a run of a scenario the stand-in has no script for fails, and says so."""
        self.scenario("R99")
        status, events = self.play(["run", "--control", "--request", self.request()])
        finished = events[-1]
        self.assertEqual(status, 1)
        self.assertEqual(finished["error"]["code"], "internal")
        self.assertIn("R99", finished["error"]["message"])

    def test_a_failed_run_keeps_the_drivers_error_whole(self) -> None:
        """standin.fail: a script's failure is the Driver's error object, retryAfterSeconds included."""
        self.scenario("selftest fail")
        status, events = self.play(["run", "--control", "--request", self.request()])
        finished = events[-1]
        self.assertEqual(status, 1)
        self.assertEqual(finished["error"], {"code": "rate_limited", "message": "Rate limited.", "retryable": True,
                                             "retryAfterSeconds": 1800})

    def test_info_names_contract_1_and_the_build(self) -> None:
        """standin.info: `-v <build> info` names the Driver of the launcher, the build and contract 1."""
        process = self.start(["-v", "7", "info"], launcher="arbol-codex-driver")
        output, _ = process.communicate(timeout=30)
        info = json.loads(output)
        self.assertEqual((info["driver"], info["build"], info["contract"]), ("codex", "7", 1))
        self.assertEqual(self.received()[0]["arguments"], ["-v", "7", "info"])
        self.assertEqual(self.received()[0]["launcher"], "arbol-codex-driver")

    def test_runs_stop_stops_a_run_from_another_invocation(self) -> None:
        """standin.runs-stop: `runs stop <run>` stops the run of that identifier; an unknown run is no error."""
        self.scenario("selftest stop")
        process = self.start(["run", "--control", "--request", self.request(runId="run-9")])
        self.events_until(process, "tool_started")
        stop = self.start(["runs", "stop", "run-9"])
        self.assertEqual(stop.wait(30), 0)
        self.assertEqual(self.events_until(process, "finished")[-1]["outcome"], "cancelled")
        self.assertEqual(process.wait(15), 2)
        began = time.monotonic()
        self.assertEqual(self.start(["runs", "stop", "run-404"]).wait(30), 0)
        self.assertLess(time.monotonic() - began, 10)

    def test_an_unknown_option_is_refused_as_the_only_event(self) -> None:
        """standin.refuses: an option a Driver does not take is refused in one finished event with invalid_input."""
        self.scenario("selftest plain")
        process = self.start(["run", "--colour", "red"])
        output, _ = process.communicate(timeout=30)
        events = [json.loads(line) for line in output.decode().splitlines()]
        self.assertEqual(process.returncode, 1)
        self.assertEqual([(event["type"], event["error"]["code"]) for event in events], [("finished", "invalid_input")])


if __name__ == "__main__":
    unittest.main()
