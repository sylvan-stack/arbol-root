# Test implementations moved to tests/mid/archived/contract/conformance/rct_conformance/scenarios/r11.py.
"""R11: whole Driver errors, missing launchers, and a folder that becomes read-only."""

from __future__ import annotations

import json
import os
import time

from ..home import ROUTE, TIME_SCALE, ScenarioHome
from ..judge import check, equal, wait_until
from .r1 import END_SECONDS, accepted
from .r13 import settled, tables


def run(home: ScenarioHome) -> None:
    raise RuntimeError('Tests are commented under the tier policy; see TESTS.md. Restore only in an explicitly requested testing task.')  # TEST-TIER-REFUSAL


def driver_failures(home: ScenarioHome) -> None:
    for code in ("rate_limited", "not_signed_in"):
        home.part(code)
        before = len(home.received())
        started = home.start()
        accepted(started)
        equal(started.process.wait(timeout=END_SECONDS), 1, "The failed Trunk's exit status")
        records = home.received()[before:]
        equal(len(records), 1, "Exactly one Driver run, with no route retry")
        equal((records[0]["launcher"], records[0]["request"]["subscriptionId"], records[0]["request"]["model"]),
              ("arbol-claude-driver", ROUTE["subscription"], ROUTE["model"]), "The Driver keeps the handed route")
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
        check(f"arbol-{driver}-driver" in row["error"]["message"], "The cause does not name the launcher.")
        equal(len(home.received()), before, "No Driver started for the missing launcher")
        equal(home.folders(hidden=True), [], "No folder remains for the missing launcher")


def folder_failure(home: ScenarioHome) -> None:
    home.part("folder")
    started = home.start()
    accepted(started)
    exchange = started.exchange
    wait_until(lambda: home.children() and any(line.get("event", {}).get("type") == "tool_started"
                                               for line in home.events(exchange)), END_SECONDS, "the running tool")
    folder = home.exchanges_folder / exchange
    os.chmod(folder, 0o500)  # prevents the whole-record replacement even with events.jsonl already open
    began = time.monotonic()
    try:
        equal(started.process.wait(timeout=END_SECONDS), 1, "The unwritable folder's exit status")
        check(time.monotonic() - began < 18 / TIME_SCALE + 2,
              "The folder failure did not stop the run within the stop budget.")
        check(folder.is_dir(), "The unwritable folder was removed.")
        row = home.rows(f"SELECT state, error FROM exchanges WHERE id = '{exchange}'")[0]
        equal((row["state"], row["error"]["code"]), ("failed", "folder_unwritable"), "The folder failure's end")
        calls = home.rows(f"SELECT ok, interrupted FROM tool_calls WHERE exchange_id = '{exchange}'")
        equal(calls, [{"ok": False, "interrupted": True}], "The held call was saved directly")
        equal(home.rows(f"SELECT outcome FROM runs WHERE exchange_id = '{exchange}'"),
              [{"outcome": "cancelled"}], "The stopped run was saved directly")
        records = [record for record in home.received() if record["request"]["runId"].startswith(exchange)]
        equal(len(records), 1, "One Driver was stopped")
        check(any(line.get("type") == "stop" for line in records[0]["control"]),
              "The Driver did not receive a stop line.")
        for child in home.children():
            try:
                os.kill(child, 0)
            except ProcessLookupError:
                continue
            check(False, "A stopped Driver's child still lives.")
        before = tables(home, exchange)
    finally:
        os.chmod(folder, 0o700)
    settled(home.run(["settle", exchange]), exchange, "failed")
    equal(tables(home, exchange), before, "Settling preserves the saved failure and all rows")
    check(exchange not in home.folders(hidden=True), "Settling left the recovered folder.")
