"""R2: foreground lines and exit statuses, an unread output pipe, and Ctrl-C (RCT-2.5, 2.8, 2.19)."""

from __future__ import annotations

import json
import os
import signal
import uuid

from ..home import ROUTE, ScenarioHome
from ..judge import check, equal, parse_line, wait_until
from .r1 import END_SECONDS, MESSAGE, accepted


def run(home: ScenarioHome) -> None:
    foreground(home)
    unread(home)
    interrupt(home)


def foreground(home: ScenarioHome) -> None:
    for outcome, status in (("completed", 0), ("failed", 1), ("cancelled", 2)):
        home.part(outcome)
        started = home.start(MESSAGE, detach=False)
        accepted(started)
        follow = home.follow(started.exchange)
        try:
            home.release()
            output, _ = started.process.communicate(timeout=END_SECONDS)
            lines = follow.lines()
        finally:
            follow.close()
        equal(started.process.returncode, status, f"{outcome}: the foreground exit status")
        equal([parse_line(line) for line in output.decode().splitlines()], lines,
              f"{outcome}: standard output after acceptance is every line of events.jsonl")
        check(lines and lines[-1].get("end", {}).get("state") == outcome,
              f"{outcome}: the file has no end with that state.", outcome, lines[-1:] or lines)
        equal(home.rows(f"SELECT state FROM exchanges WHERE id = '{started.exchange}'"),
              [{"state": outcome}], f"{outcome}: the saved Exchange")


def unread(home: ScenarioHome) -> None:
    home.part("unread")
    exchange = str(uuid.uuid4())
    file = home.request_file({"message": MESSAGE, "route": ROUTE})
    process = home.spawn(["run", "--exchange", exchange, "--request", str(file)])
    wait_until(lambda: exchange in home.folders(), END_SECONDS, "unread: the Exchange folder")
    follow = home.follow(exchange)
    try:
        home.release()
        process.wait(timeout=END_SECONDS)  # do not read even the acceptance until the process has ended
        assert process.stdout is not None
        output = process.stdout.read().decode().splitlines()
        process.stdout.close()
        lines = follow.lines()
    finally:
        follow.close()
        file.unlink(missing_ok=True)
    equal(process.returncode, 0, "unread: the exit status")
    answer = json.loads(output[0])
    check(answer.get("accepted") is True, "unread: the first line is no acceptance.", True, answer)
    home.ran(exchange, answer["chat"])
    check(len(lines) > len(output), "unread: the test did not fill the output pipe.")
    equal(lines[-1].get("end", {}).get("state"), "completed", "unread: the file's end")
    equal(home.rows(f"SELECT state FROM exchanges WHERE id = '{exchange}'"),
          [{"state": "completed"}], "unread: the saved Exchange")


def interrupt(home: ScenarioHome) -> None:
    home.part("interrupt")
    started = home.start(MESSAGE, detach=False)
    accepted(started)
    exchange = started.exchange
    wait_until(lambda: any(line.get("event", {}).get("type") == "tool_started" for line in home.events(exchange)),
               END_SECONDS, "Ctrl-C: the running tool call")
    os.killpg(started.process.pid, signal.SIGINT)
    started.process.wait(timeout=END_SECONDS)
    assert started.process.stdout is not None
    started.process.stdout.close()
    check(exchange in home.folders(), "Ctrl-C removed the Exchange's folder before settling.")
    check("end" not in home.record(exchange), "Ctrl-C wrote an end in the record.")
    check(all("end" not in line for line in home.events(exchange)), "Ctrl-C wrote an end in events.jsonl.")
    settled = home.run(["settle", exchange])
    equal(settled.status, 0, "Ctrl-C: the settle exit status")
    equal(settled.output, [{"exchange": exchange, "settled": "interrupted"}], "Ctrl-C: the settle answer")
    equal(home.rows(f"SELECT state FROM exchanges WHERE id = '{exchange}'"),
          [{"state": "interrupted"}], "Ctrl-C: the saved Exchange")
    check(exchange not in home.folders(hidden=True), "Ctrl-C: the settled folder remains.")
