# Test implementations moved to tests/mid/archived/contract/conformance/tests/test_standin.py.
"""The stand-in Driver (RCT-4, "The stand-in Driver"), started through its launchers as a Trunk starts a Driver: it
plays a script, writes events as a Driver does, stops a run as a Driver does, and records each start."""

from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from typing import IO, Any

from rct_conformance.home import SYSTEM_PATH, write_launchers
from rct_conformance.judge import json_lines


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














if __name__ == "__main__":
    unittest.main()

# Archived complete imports; restore needed names in their original scope, not at this file tail.
