"""R17: original event bytes, NUL and split emoji replacements in SQL, and independent tool flags."""

from __future__ import annotations
import json

from ..home import ROUTE, ScenarioHome
from ..judge import check, equal
from .r1 import END_SECONDS, accepted


from ..home import ScenarioHome

MESSAGE = "Original\0message \ud83d and 😀."
STORED_MESSAGE = "Original�message � and 😀."
MODEL = "standin😀\0\ud83d"
STORED_MODEL = "standin😀��"


def run(home: ScenarioHome) -> None:
    home.part()
    started = home.start(MESSAGE, request={"route": {**ROUTE, "model": MODEL},
                                          "smallCallRoute": {"driver": "codex", "model": MODEL}})
    accepted(started)
    exchange = started.exchange
    follow = home.follow(exchange)
    try:
        home.release()
        equal(started.process.wait(timeout=END_SECONDS), 0, "The character scenario completes")
        lines = follow.lines()
    finally:
        follow.close()
    records = home.received()
    equal(len(records), 1, "One Driver run")
    equal(records[0]["request"]["input"]["text"], MESSAGE, "The Driver gets the original message")
    written = [json.loads(raw) for raw in records[0]["events"]]
    equal([line["event"] for line in lines[:-1]], written, "The file preserves every original event value")
    raw_lines = follow.data.decode("utf-8").splitlines()
    equal(raw_lines[:-1], [f'{{"n":{n},"event":{raw}}}' for n, raw in enumerate(records[0]["events"], 1)],
          "The file preserves the exact event JSON")
    equal(lines[-1]["end"]["state"], "completed", "The file's end")
    equal(home.rows(f"SELECT role, text FROM messages WHERE exchange_id = '{exchange}' ORDER BY position"),
          [{"role": "user", "text": STORED_MESSAGE}, {"role": "assistant", "text": "A whole 😀 stays whole."},
           {"role": "assistant", "text": "�"}, {"role": "assistant", "text": "�"}], "Only invalid characters change")
    equal(home.rows(f"SELECT name, input, ok, result, interrupted FROM tool_calls WHERE exchange_id = '{exchange}'"),
          [{"name": "shell", "input": {"command": "cat binary", "nested": {"key�": ["�", "😀"]}}, "ok": True,
            "result": {"output": "before�after 😀", "exitCode": 0}, "interrupted": True}],
          "JSON keys, nested strings, NUL output and both flags")
    row = home.rows(f"SELECT state, route, small_call_route FROM exchanges WHERE id = '{exchange}'")[0]
    equal(row, {"state": "completed", "route": {**ROUTE, "model": STORED_MODEL},
                "small_call_route": {"driver": "codex", "model": STORED_MODEL}}, "Both stored routes are safe")
    run_row = home.rows(f"SELECT usage, started FROM runs WHERE exchange_id = '{exchange}'")[0]
    equal(run_row["usage"], {"model": STORED_MODEL, "inputTokens": 1, "outputTokens": 2}, "Safe usage JSON")
    equal(run_row["started"]["model"], STORED_MODEL, "Safe started JSON")
    check(exchange not in home.folders(hidden=True), "Invalid characters left the chat busy.")

# Archived complete imports; restore needed names in their original scope, not at this file tail.
