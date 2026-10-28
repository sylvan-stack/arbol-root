"""R15: bound each tool's streamed output and the whole file while keeping complete closing lines."""

from __future__ import annotations

import json

from ..home import ScenarioHome
from ..judge import check, equal
from .r1 import END_SECONDS, accepted

MIB = 1024 * 1024


# TEST-TIER-DISABLED-BEGIN contract/conformance/rct_conformance/scenarios/r15.py::run
# def run(home: ScenarioHome) -> None:
#     tool_output(home)
#     whole_file(home)
# TEST-TIER-DISABLED-END contract/conformance/rct_conformance/scenarios/r15.py::run
def run(home: ScenarioHome) -> None:
    raise RuntimeError('Tests are commented under the tier policy; see TESTS.md. Restore only in an explicitly requested testing task.')  # TEST-TIER-REFUSAL


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


def whole_file(home: ScenarioHome) -> None:
    home.part("file")
    started = home.start()
    accepted(started)
    exchange = started.exchange
    follow = home.follow(exchange)
    starts: dict[str, int] = {}
    closed: set[str] = set()
    total = 0
    closing_bytes = 0
    count = 0
    previous_seq = 0
    limited = False
    end = None
    try:
        home.release()
        equal(started.process.wait(timeout=120), 1, "The full-file Trunk's exit status")
        for raw in follow.stream:  # inspect the full 256 MiB without keeping it in the judge's memory
            check(raw.endswith(b"\n"), "The full file has an unfinished line.")
            check(end is None, "A line follows the Exchange end.")
            total += len(raw)
            count += 1
            line = json.loads(raw)
            equal(line["n"], count, "The full file's consecutive n")
            event = line.get("event")
            if isinstance(event, dict):
                kind = event["type"]
                seq = event["seq"]
                if seq > previous_seq + 1:
                    limited = True
                previous_seq = seq
                if kind == "tool_started":
                    starts[event["callId"]] = count
                if kind == "tool_finished":
                    check(event["callId"] in starts, "A closing call has no written start.")
                    closed.add(event["callId"])
                if limited:
                    check(kind in ("tool_finished", "ask_closed", "usage", "finished"),
                          "The full file kept a new non-closing event.")
                if kind in ("tool_finished", "ask_closed", "usage", "finished"):
                    closing_bytes += len(raw)
            elif "end" in line:
                end = line["end"]
                closing_bytes += len(raw)
            else:
                check(False, "An unexpected line followed the file limit.")
    finally:
        follow.close()
    check(limited, "No streamed event was omitted at the whole-file cap.")
    check(256 * MIB - 128 * 1024 <= total <= 256 * MIB + closing_bytes,
          "The events file was not bounded at 256 MiB plus closing lines.", 256 * MIB, total)
    check(isinstance(end, dict), "The full file has no end.")
    assert end is not None
    equal((end["state"], end["error"]["code"]), ("failed", "events_file_full"), "The full file's failure")
    equal(sorted(closed), sorted(starts), "Every started call got its closing line")
    rows = home.rows(f"SELECT position, ok, interrupted FROM tool_calls WHERE exchange_id = '{exchange}' ORDER BY position")
    equal(len(rows), 2, "Both calls were saved")
    check(all(row["position"] in starts.values() for row in rows), "A saved call has no start in the file.")
    equal([(row["ok"], row["interrupted"]) for row in rows], [(True, False), (False, True)],
          "The completed and interrupted calls remain truthful")
    equal(home.rows(f"SELECT text FROM messages WHERE exchange_id = '{exchange}' AND position > 0"),
          [{"text": "Saved before the file filled."}], "What finished before the cap was saved")
    row = home.rows(f"SELECT state, error FROM exchanges WHERE id = '{exchange}'")[0]
    equal((row["state"], row["error"]["code"]), ("failed", "events_file_full"), "The saved full-file failure")
    check(exchange not in home.folders(hidden=True), "The full file was not saved and removed.")
