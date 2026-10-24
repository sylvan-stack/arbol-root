"""R10: SIGTERM leaves no end; settling recovers the text, open call and interrupted run (RCT-2.8, 2.12)."""

from __future__ import annotations

import os
import signal
import subprocess
from datetime import UTC, datetime

from ..home import ScenarioHome
from ..judge import check, equal, wait_until
from .r1 import END_SECONDS, MESSAGE, accepted


def group_alive(group: int) -> bool:
    output = subprocess.run(["/bin/ps", "-A", "-o", "pgid=,stat="], capture_output=True, text=True,
                            check=False).stdout
    return any(parts[0] == str(group) and not parts[1].startswith("Z")
               for line in output.splitlines() if len(parts := line.split()) == 2)


def run(home: ScenarioHome) -> None:
    home.part()
    started = home.start(MESSAGE)
    accepted(started)
    exchange = started.exchange
    wait_until(lambda: any(line.get("event", {}).get("type") == "tool_started" for line in home.events(exchange)),
               END_SECONDS, "SIGTERM: the running tool call")
    children = home.children()
    check(children, "The stand-in did not start its separate child process group.")
    os.killpg(started.process.pid, signal.SIGTERM)
    started.process.wait(timeout=END_SECONDS)
    wait_until(lambda: not any(group_alive(group) for group in [started.process.pid, *children]), END_SECONDS,
               "SIGTERM: the Trunk and child groups to end")
    received = wait_until(home.received, END_SECONDS, "SIGTERM: the stand-in's record")
    check("SIGTERM" in received[0]["signals"], "The stand-in did not receive SIGTERM.",
          "SIGTERM", received[0]["signals"])
    record, lines = home.record(exchange), home.events(exchange)
    check(record is not None and "end" not in record, "SIGTERM wrote an end or removed the folder.")
    check(all("end" not in line for line in lines), "SIGTERM wrote an end in events.jsonl.")
    events = [line["event"] for line in lines if "event" in line]
    check(not any(event["type"] == "finished" for event in events), "The run ended before the signal reached it.")
    text = next(line for line in lines if line.get("event", {}).get("type") == "text")
    call = next(line for line in lines if line.get("event", {}).get("type") == "tool_started")
    usage = next(event["usage"] for event in events if event["type"] == "usage")
    last_at = datetime.fromisoformat(events[-1]["at"])
    equal(home.rows(f"SELECT state FROM exchanges WHERE id = '{exchange}'"), [{"state": "open"}],
          "SIGTERM: the Exchange before settling")

    settled = home.run(["settle", exchange])
    equal((settled.status, settled.output), (0, [{"exchange": exchange, "settled": "interrupted"}]),
          "SIGTERM: the settle answer")
    equal(home.rows(f"SELECT position, text FROM messages WHERE exchange_id = '{exchange}' AND role = 'assistant'"),
          [{"position": text["n"], "text": text["event"]["text"]}], "SIGTERM: the recovered text")
    equal(home.rows(f"SELECT position, name, input, ok, interrupted FROM tool_calls WHERE exchange_id = '{exchange}'"),
          [{"position": call["n"], "name": call["event"]["name"], "input": call["event"]["input"],
            "ok": False, "interrupted": True}], "SIGTERM: the interrupted tool call")
    runs = home.rows(f"SELECT kind, outcome, usage, ended_at FROM runs WHERE exchange_id = '{exchange}'")
    equal([{key: value for key, value in row.items() if key != "ended_at"} for row in runs],
          [{"kind": "agent", "outcome": "interrupted", "usage": usage}], "SIGTERM: the interrupted run")
    equal(datetime.fromisoformat(runs[0]["ended_at"]).astimezone(UTC).isoformat(), last_at.isoformat(),
          "SIGTERM: the run's end is the last event time")
    ended = home.rows(f"SELECT state, error, ended_at FROM exchanges WHERE id = '{exchange}'")[0]
    equal((ended["state"], ended["error"], datetime.fromisoformat(ended["ended_at"]).astimezone(UTC).isoformat()),
          ("interrupted", None, last_at.isoformat()), "SIGTERM: the recovered Exchange")
    check(exchange not in home.folders(hidden=True), "SIGTERM: the settled folder remains.")
