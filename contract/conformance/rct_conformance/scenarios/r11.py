"""R11: whole Driver errors, missing launchers, and a folder that becomes read-only."""

from __future__ import annotations

import json

from ..home import ROUTE, ScenarioHome
from ..judge import equal
from .r1 import END_SECONDS, accepted


def run(home: ScenarioHome) -> None:
    driver_failures(home)


def driver_failures(home: ScenarioHome) -> None:
    for code in ("rate_limited", "not_signed_in"):
        home.part(code)
        before = len(home.received())
        started = home.start()
        accepted(started)
        equal(started.process.wait(timeout=END_SECONDS), 1, "The failed Trunk's exit status")
        records = home.received()[before:]
        equal(len(records), 1, "Exactly one Driver run, with no route retry")
        finished = next(json.loads(raw) for raw in records[0]["events"] if json.loads(raw)["type"] == "finished")
        error = finished["error"]
        equal(error["code"], code, "The Driver's error code")
        if code == "rate_limited":
            equal(error["retryAfterSeconds"], 1800, "The whole rate limit error")
        else:
            equal(len(records[0]["events"]), 1, "The refusal was the only event")
        equal(home.rows(f"SELECT state, error FROM exchanges WHERE id = '{started.exchange}'"),
              [{"state": "failed", "error": error}], "The Exchange keeps the Driver's whole cause")
        equal(home.rows(f"SELECT kind, outcome, error FROM runs WHERE exchange_id = '{started.exchange}'"),
              [{"kind": "agent", "outcome": "failed", "error": error}], "The one failed run")
        equal(home.folders(hidden=True), [], "The failed Exchange's folder was removed")

    for driver in ("missing", "some/path"):
        before = len(home.received())
        started = home.start(request={"route": {**ROUTE, "driver": driver}})
        accepted(started)
        equal(started.process.wait(timeout=END_SECONDS), 1, "The missing launcher's exit status")
        row = home.rows(f"SELECT state, error FROM exchanges WHERE id = '{started.exchange}'")[0]
        equal((row["state"], row["error"]["code"]), ("failed", "driver_failed"), "The missing launcher fails")
        from ..judge import check
        check(f"arbol-{driver}-driver" in row["error"]["message"], "The cause does not name the launcher.")
        equal(len(home.received()), before, "No Driver started for the missing launcher")
        equal(home.folders(hidden=True), [], "No folder remains for the missing launcher")
