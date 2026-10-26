"""R15: bound each tool's streamed output and the whole file while keeping complete closing lines."""

from __future__ import annotations

import json

from ..home import ScenarioHome
from ..judge import check, equal
from .r1 import END_SECONDS, accepted

MIB = 1024 * 1024


def run(home: ScenarioHome) -> None:
    tool_output(home)


def tool_output(home: ScenarioHome) -> None:
    home.part("tool")
    started = home.start()
    accepted(started)
    exchange = started.exchange
    follow = home.follow(exchange)
    try:
        home.release()
        equal(started.process.wait(timeout=END_SECONDS), 0, "The limited tool-output Exchange completes")
        lines = follow.lines()
    finally:
        follow.close()
    record = home.received()[0]
    driver_events = [json.loads(raw) for raw in record["events"]]
    driver_output = [event for event in driver_events if event["type"] == "tool_output_delta"]
    equal(sum(len(event["text"].encode()) for event in driver_output), 2 * MIB, "The stand-in streamed two MiB")
    raw = follow.data.splitlines(keepends=True)
    output = [line for line in raw if json.loads(line).get("event", {}).get("type") == "tool_output_delta"]
    total = sum(map(len, output))
    check(MIB < total <= MIB + max(map(len, output)), "The tool output did not stop at about one MiB.", MIB, total)
    equal([line["n"] for line in lines], list(range(1, len(lines) + 1)), "Omitted output takes no n")
    equal([line["event"] for line in lines[:-1] if line["event"]["type"] != "tool_output_delta"],
          [event for event in driver_events if event["type"] != "tool_output_delta"], "All other events remain exact")
    equal(lines[-1]["end"]["state"], "completed", "The completed file end")
    equal(home.rows(f"SELECT name, ok, truncated, result FROM tool_calls WHERE exchange_id = '{exchange}'"),
          [{"name": "shell", "ok": True, "truncated": True, "result": {"output": "x" * (200 * 1024), "exitCode": 0}}],
          "The call retains its bounded result")
    equal(home.rows(f"SELECT text FROM messages WHERE exchange_id = '{exchange}' AND position > 0"),
          [{"text": "The large log was read."}], "Text after the capped output is saved")
    equal(home.rows(f"SELECT state FROM exchanges WHERE id = '{exchange}'"), [{"state": "completed"}],
          "The stored end")
    check(exchange not in home.folders(hidden=True), "The limited tool output left its folder.")
