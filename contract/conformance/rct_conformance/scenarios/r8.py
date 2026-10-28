"""R8: stop (RCT-4).

A stop line while text streams, while a tool call runs, while a question is open, and one written while the folder
still has its dot name. The suite judges: the stand-in got the line unchanged; the end `cancelled` in the folder within
18 seconds (divided); the running call saved as interrupted; the Exchange cancelled; the folder gone; for the early stop,
no run started.

Covers RCT-1.7 and 2.7.
"""

from __future__ import annotations

import time
import uuid
from collections.abc import Callable
from typing import Any

from ..home import TIME_SCALE, Follow, ScenarioHome
from ..judge import check, equal, wait_until
from .r1 import END_SECONDS, accepted

MESSAGE = "Build the packages."
STOP = {"type": "stop"}
STOP_SECONDS = 18.0 / TIME_SCALE  # RCT-2.7: the end is in the folder within 18 seconds of the stop line, divided
INTERRUPTED = {"ok": False, "interrupted": True}
WRITER_SECONDS = 15.0  # RCT-1.8: how long a writer waits for the folder to be in place


# TEST-TIER-DISABLED-BEGIN contract/conformance/rct_conformance/scenarios/r8.py::run
# def run(home: ScenarioHome) -> None:
#     stopped(home, "text", lambda events: len([e for e in events if e.get("type") == "text_delta"]) >= 2)
#     calls = stopped(home, "tool", lambda events: any(e.get("type") == "tool_started" for e in events))
#     equal([{key: call[key] for key in ("name", "ok", "interrupted")} for call in calls],
#           [{"name": "shell", **INTERRUPTED}], "tool: the shell call that was running")
#     asks: list[Any] = []
#
#     def asked(events: list[dict[str, Any]]) -> bool:
#         asks[:] = [event["ask"] for event in events if event.get("type") == "ask_opened"]
#         return bool(asks)
#
#     calls = stopped(home, "ask", asked)
#     equal(calls, [{"name": "ask_user", **INTERRUPTED, "ask": asks[0], "answer": None}],
#           "ask: the question that was open")
#     early(home)
# TEST-TIER-DISABLED-END contract/conformance/rct_conformance/scenarios/r8.py::run
def run(home: ScenarioHome) -> None:
    raise RuntimeError('Tests are commented under the tier policy; see TESTS.md. Restore only in an explicitly requested testing task.')  # TEST-TIER-REFUSAL


def early(home: ScenarioHome) -> None:
    """A stop line written from the moment the Trunk is started, as a writer that finds the folder under its dot
    name waits for it to be in place (RCT-1.8), while every acceptance is held, so that the line is in `control`
    before the Trunk could start its run (RCT-D35): no run starts, and the Exchange ends as cancelled."""
    home.part("early")
    exchange = str(uuid.uuid4())
    control = home.exchanges_folder / exchange / "control"
    follows: list[Follow] = []
    written: list[float] = []
    with home.acceptances_held() as held:
        def meanwhile() -> None:
            wait_until(control.exists, WRITER_SECONDS, "early: the Exchange's control in place", every=0.005)
            follows.append(home.follow(exchange))
            home.control(exchange, STOP)
            written.append(time.monotonic())
            held.release()

        started = home.start(MESSAGE, exchange=exchange, meanwhile=meanwhile)
    accepted(started)
    try:
        lines = wait_until(lambda: ended(follows[0]), END_SECONDS, "early: the end in the folder", every=0.01)
        took = time.monotonic() - written[0]
    finally:
        follows[0].close()
    equal([line.get("end", {}).get("state") for line in lines], ["cancelled"], "early: the lines of events.jsonl")
    check(took <= STOP_SECONDS, f"early: the end came {took:.2f} s after the stop line.",
          f"within {STOP_SECONDS:g} s", round(took, 2))
    wait_until(lambda: exchange not in home.folders(hidden=True), END_SECONDS, "early: the folder to go")
    equal([record for record in home.received() if record.get("part") == "early"], [],
          "early: the starts of the stand-in")
    equal(home.rows(f"SELECT state, error FROM exchanges WHERE id = '{exchange}'"),
          [{"state": "cancelled", "error": None}], "early: the Exchange")
    equal(home.rows(f"SELECT run_id FROM runs WHERE exchange_id = '{exchange}'"), [], "early: the runs")


def ended(follow: Follow) -> list[Any] | None:
    """The lines of `events.jsonl` once its last line is the end."""
    found = follow.lines()
    return found if found and isinstance(found[-1], dict) and "end" in found[-1] else None


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
        home.control(exchange, STOP)
        written = time.monotonic()
        lines = wait_until(lambda: ended(follow), END_SECONDS, f"{part}: the end in the folder", every=0.01)
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
