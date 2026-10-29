"""R18: after sixteen idle minutes on the divided awake clock, stop even with a background command."""

from __future__ import annotations
import time

from ..home import TIME_SCALE, ScenarioHome
from ..judge import check, equal, wait_until
from .r1 import END_SECONDS, accepted
from .r10 import group_alive


from ..home import ScenarioHome

IDLE_SECONDS = 16 * 60


def run(home: ScenarioHome) -> None:
    home.part()
    started = home.start()
    accepted(started)
    exchange = started.exchange
    wait_until(lambda: any(line.get("event", {}).get("type") == "usage" for line in home.events(exchange)),
               END_SECONDS, "the last event before silence")
    children = wait_until(home.children, END_SECONDS, "the background command")
    follow = home.follow(exchange)
    began = time.monotonic()
    before = home.record(exchange)["signsOfLife"]["heartbeat"]
    try:
        # There is deliberately no event and no control write from the suite during the idle interval.
        equal(started.process.wait(timeout=(IDLE_SECONDS + 18) / TIME_SCALE + 5), 1, "The silent Trunk's exit status")
        elapsed = time.monotonic() - began
        check((IDLE_SECONDS - 10) / TIME_SCALE <= elapsed <= (IDLE_SECONDS + 18) / TIME_SCALE + 5,
              "Silence did not use sixteen minutes plus the bounded stop.", IDLE_SECONDS / TIME_SCALE, elapsed)
        lines = follow.lines()
    finally:
        follow.close()
    end = lines[-1]["end"]
    equal((end["state"], end["error"]["code"]), ("failed", "driver_silent"), "The silent Exchange's end")
    records = home.received()
    equal(len(records), 1, "Exactly one Driver run")
    check(any(line.get("type") == "stop" for line in records[0]["control"]), "The silent Driver got no stop line.")
    check(not any(group_alive(child) for child in children), "The stopped Driver left its background command alive.")
    row = home.rows(f"SELECT state, error FROM exchanges WHERE id = '{exchange}'")[0]
    equal((row["state"], row["error"]["code"]), ("failed", "driver_silent"), "The saved silent failure")
    equal(home.rows(f"SELECT outcome, usage FROM runs WHERE exchange_id = '{exchange}'"),
          [{"outcome": "cancelled", "usage": {"model": "standin-model", "inputTokens": 7, "outputTokens": 3}}],
          "The stopped run retains its usage")
    equal(home.rows(f"SELECT text FROM messages WHERE exchange_id = '{exchange}' AND position > 0"),
          [{"text": "Half an answer before silence."}], "The partial answer was saved")
    check(before > 0, "The work loop never raised its initial heartbeat.")
    check(exchange not in home.folders(hidden=True), "The silent Exchange left its folder.")

# Archived complete imports; restore needed names in their original scope, not at this file tail.
