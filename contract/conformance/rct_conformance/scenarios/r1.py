# Test implementations moved to tests/mid/archived/contract/conformance/rct_conformance/scenarios/r1.py.
"""R1: a plain answer in the background (RCT-4).

The stand-in writes text, a `shell` call, more text and usage, and completes. The suite judges: one acceptance line,
and when it came the folder, the chat, the open Exchange and the message at position 0 were there; the process lived on
after the suite closed its end of the pipe; the stand-in was started through its launcher name with `--control`; `n`
from 1 without gaps, every event as the stand-in wrote it, the end last; the rows at their positions, the run of the kind
`agent` with its usage and its `started` event; the Exchange completed; the folder gone.

Covers RCT-0.4, 0.6, 0.14, 1.1, 1.2, 1.5, 2.1, 2.4, 2.9, 2.20, 3.1, 3.2 and 3.3.
"""

from __future__ import annotations

import re
from datetime import datetime
from typing import Any

from ..home import ROOT, ScenarioHome, Started
from ..judge import check, equal

MESSAGE = "What does build.sh do?"
CODE_NAME = re.compile(r"[a-z][a-z0-9]{0,31}")
BUILD = re.compile(r"0|[1-9a-f][0-9a-f]*")
ACCEPTANCE_SECONDS = 15.0
END_SECONDS = 30.0


def accepted(started: Started) -> dict[str, Any]:
    """The one acceptance line of a start, judged as RCT-2's Accepted."""
    check(isinstance(started.answer, dict) and started.answer.get("accepted") is True,
          "The Trunk did not accept the message.", "an acceptance line", started.line)
    answer: dict[str, Any] = started.answer
    check(started.seconds < ACCEPTANCE_SECONDS, f"The answer came after {started.seconds:.1f} s.",
          f"within {ACCEPTANCE_SECONDS:g} s", started.seconds)
    equal(sorted(answer), sorted(["accepted", "duplicate", "root", "exchange", "chat", "number", "trunk", "build"]),
          "The fields of the acceptance line")
    equal([answer["duplicate"], answer["root"], answer["exchange"]], [False, ROOT, started.exchange],
          "duplicate, root and exchange of the acceptance line")
    check(isinstance(answer["trunk"], str) and CODE_NAME.fullmatch(answer["trunk"]), "trunk is no code name.",
          "a code name", answer["trunk"])
    check(isinstance(answer["build"], str) and BUILD.fullmatch(answer["build"]), "build is no build number.",
          "a build number", answer["build"])
    return answer


def run(home: ScenarioHome) -> None:
    raise RuntimeError('Tests are commented under the tier policy; see TESTS.md. Restore only in an explicitly requested testing task.')  # TEST-TIER-REFUSAL


def moment(value: str) -> datetime:
    return datetime.fromisoformat(value)


def judge_rows(home: ScenarioHome, exchange: str, events: list[dict[str, Any]]) -> None:
    """The rows at their positions (RCT-3), the run with its usage and its started event, the Exchange completed."""
    messages = [{"position": 0, "role": "user", "text": MESSAGE}]
    calls = []
    finished: dict[str, Any] = {}
    for n, event in enumerate(events, 1):
        if event["type"] == "text" and "parentCallId" not in event:
            messages.append({"position": n, "role": "assistant", "text": event["text"]})
        elif event["type"] == "tool_started":
            done = next(e for e in events if e["type"] == "tool_finished" and e["callId"] == event["callId"])
            calls.append({"position": n, "run_id": event["runId"], "call_id": event["callId"], "parent_call_id": None,
                          "name": event["name"], "input": event["input"], "ok": done["ok"],
                          "result": done.get("result"), "error": done.get("error"), "truncated": False,
                          "interrupted": False})
        elif event["type"] == "finished":
            finished = event
    equal(home.rows(f"SELECT position, role, text FROM messages WHERE exchange_id = '{exchange}' ORDER BY position"),
          messages, "The messages at their positions")
    equal(home.rows("SELECT position, run_id, call_id, parent_call_id, name, input, ok, result, error, truncated,"
                    f" interrupted FROM tool_calls WHERE exchange_id = '{exchange}' ORDER BY position"),
          calls, "The tool calls at their positions")
    runs = home.rows(f"SELECT run_id, kind, outcome, usage, error, started, ended_at FROM runs"
                     f" WHERE exchange_id = '{exchange}'")
    equal([{key: value for key, value in run.items() if key != "ended_at"} for run in runs],
          [{"run_id": events[0]["runId"], "kind": "agent", "outcome": "completed", "usage": finished["usage"],
            "error": None, "started": events[0]}], "The run")
    check(moment(runs[0]["ended_at"]) == moment(finished["at"]), "The run's ended_at is not its finished event's at.",
          finished["at"], runs[0]["ended_at"])
    rows = home.rows(f"SELECT state, error, ended_at IS NOT NULL AS ended FROM exchanges WHERE id = '{exchange}'")
    equal(rows, [{"state": "completed", "error": None, "ended": True}], "The Exchange at its end")

# Archived complete imports; restore needed names in their original scope, not at this file tail.
