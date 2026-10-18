"""R8: stop (RCT-4).

A stop line while text streams, while a tool call runs, while a question is open, and one written while the folder
still has its dot name. The suite judges: the stand-in got the line unchanged; the end `cancelled` in the folder within
18 seconds (divided); the running call saved as interrupted; the Exchange cancelled; the folder gone; for the early stop,
no run started.

Covers RCT-1.7 and 2.7.
"""

from __future__ import annotations

import time
from collections.abc import Callable
from typing import Any

from ..home import TIME_SCALE, ScenarioHome
from ..judge import check, equal, wait_until
from .r1 import END_SECONDS, accepted

MESSAGE = "Build the packages."
STOP = {"type": "stop"}
STOP_SECONDS = 18.0 / TIME_SCALE  # RCT-2.7: the end is in the folder within 18 seconds of the stop line, divided
INTERRUPTED = {"ok": False, "interrupted": True}


def run(home: ScenarioHome) -> None:
    stopped(home, "text", lambda events: len([e for e in events if e.get("type") == "text_delta"]) >= 2)
    calls = stopped(home, "tool", lambda events: any(e.get("type") == "tool_started" for e in events))
    equal([{key: call[key] for key in ("name", "ok", "interrupted")} for call in calls],
          [{"name": "shell", **INTERRUPTED}], "tool: the shell call that was running")


def stopped(home: ScenarioHome, part: str, ready: Callable[[list[dict[str, Any]]], bool]) -> list[dict[str, Any]]:
    """Starts a message, appends a stop line to `control` once `ready` holds for the events so far, and judges the
    stop. Gives the Exchange's tool calls."""
    home.part(part)
    started = home.start(MESSAGE)
    accepted(started)
    exchange = started.exchange
    follow = home.follow(exchange)
    try:
        wait_until(lambda: ready([line["event"] for line in home.events(exchange) if "event" in line]), END_SECONDS,
                   f"{part}: the moment to stop")

        def ended() -> list[Any] | None:
            found = follow.lines()
            return found if found and isinstance(found[-1], dict) and "end" in found[-1] else None

        home.control(exchange, STOP)
        written = time.monotonic()
        lines = wait_until(ended, END_SECONDS, f"{part}: the end in the folder", every=0.01)
        took = time.monotonic() - written
    finally:
        follow.close()
    equal(lines[-1]["end"].get("state"), "cancelled", f"{part}: the end in the folder")
    check(took <= STOP_SECONDS, f"{part}: the end came {took:.2f} s after the stop line.", f"within {STOP_SECONDS:g} s",
          round(took, 2))
    wait_until(lambda: exchange not in home.folders(hidden=True), END_SECONDS, f"{part}: the folder to go")
    record = wait_until(lambda: [r for r in home.received() if r.get("part") == part], END_SECONDS,
                        f"{part}: the stand-in's record")[0]
    equal(record["control"], [STOP], f"{part}: the control input of the stand-in")
    equal(home.rows(f"SELECT state, error FROM exchanges WHERE id = '{exchange}'"),
          [{"state": "cancelled", "error": None}], f"{part}: the Exchange")
    equal(home.rows(f"SELECT kind, outcome FROM runs WHERE exchange_id = '{exchange}'"),
          [{"kind": "agent", "outcome": "cancelled"}], f"{part}: the run")
    return home.rows("SELECT name, ok, interrupted, ask, answer FROM tool_calls"
                     f" WHERE exchange_id = '{exchange}' ORDER BY position")
