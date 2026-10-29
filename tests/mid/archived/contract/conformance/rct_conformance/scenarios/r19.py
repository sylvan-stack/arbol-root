"""R19: small calls (RCT-4).

Three parts: a start without a small-call route; one with a route whose small call completes; one whose small call
fails. The suite judges: without a route, no run with `"tools": "none"`; a small call that ran was a run with
`"tools": "none"` on the route handed, and left a `smallRun` line and a `runs` row of the kind `small` with its usage;
the Exchange completed in every part. A Trunk that makes no small call passes when every part completes.

Covers RCT-1.11 and 2.22.
"""

from __future__ import annotations

from ..judge import check, equal, wait_until
from .r1 import END_SECONDS, accepted


from collections.abc import Callable
from typing import Any

from ..home import ScenarioHome

SMALL_ROUTE = {"driver": "claude", "subscription": "standin", "model": "standin-small"}
PARTS: dict[str, dict[str, str] | None] = {"none": None, "completes": SMALL_ROUTE, "fails": SMALL_ROUTE}


def small_calls(records: list[Any]) -> list[Any]:
    return [record for record in records if isinstance(record.get("request"), dict)
            and record["request"].get("tools") == "none" and not record["request"].get("chatSessionId")]


def folder_gone(home: ScenarioHome, exchange: str) -> Callable[[], bool]:
    return lambda: exchange not in home.folders(hidden=True)


def run(home: ScenarioHome) -> None:
    for part, route in PARTS.items():
        home.part(part)
        started = home.start("Name this chat.", request={"smallCallRoute": route} if route else None)
        exchange = accepted(started)["exchange"]
        follow = home.follow(exchange)
        try:
            record = home.record(exchange)
            check(isinstance(record, dict), f"{part}: the Exchange has no record once it is accepted.")
            equal(record.get("smallCallRoute"), route, f"{part}: the record's smallCallRoute")
            wait_until(folder_gone(home, exchange), END_SECONDS, f"{part}: the Exchange's folder to go")
            lines = follow.lines()
        finally:
            follow.close()
        equal(home.rows(f"SELECT state, small_call_route FROM exchanges WHERE id = '{exchange}'"),
              [{"state": "completed", "small_call_route": route}], f"{part}: the Exchange")
        smalls = small_calls([record for record in home.received() if record.get("part") == part])
        small_lines = [line["smallRun"] for line in lines if isinstance(line, dict) and "smallRun" in line]
        small_rows = home.rows(f"SELECT run_id, outcome, usage FROM runs WHERE exchange_id = '{exchange}'"
                               " AND kind = 'small' ORDER BY run_id")
        if route is None:
            equal(len(smalls), 0, f"{part}: runs with tools none without a small-call route")
        else:
            for small in smalls:
                check(small["launcher"] == f"arbol-{route['driver']}-driver"
                      and small["request"].get("subscriptionId") == route["subscription"]
                      and small["request"].get("model") == route["model"],
                      f"{part}: a small call ran on another route than the one handed.", route, small["request"])
        equal(len(small_lines), len(smalls), f"{part}: the smallRun lines of the small calls that ran")
        equal(len(small_rows), len(smalls), f"{part}: the runs of the kind small")
        for row in small_rows:
            check(isinstance(row["usage"], dict) and row["usage"], f"{part}: a small call's run has no usage.",
                  "its usage", row)

# Archived complete imports; restore needed names in their original scope, not at this file tail.
