"""R13: settling unknown, live, repeated and concurrent Exchanges, then recovery edges (RCT-2.12)."""

from __future__ import annotations

import os
import signal
import time
import uuid
from concurrent.futures import ThreadPoolExecutor
from typing import Any

from ..home import DATABASE, Completed, ScenarioHome, Started
from ..judge import check, equal, wait_until
from .r1 import END_SECONDS, MESSAGE, accepted
from .r4 import refusal


def settled(result: Completed, exchange: str, state: str) -> None:
    equal((result.status, result.output), (0, [{"exchange": exchange, "settled": state}]), "The settle answer")


def tables(home: ScenarioHome, exchange: str) -> dict[str, list[dict[str, Any]]]:
    return {table: home.rows(f"SELECT * FROM {table} WHERE {key} = '{exchange}' ORDER BY {order}")
            for table, key, order in (("exchanges", "id", "id"), ("messages", "exchange_id", "position"),
                                      ("tool_calls", "exchange_id", "position"), ("runs", "exchange_id", "run_id"))}


def interrupt(home: ScenarioHome) -> Started:
    home.part("interrupted")
    started = home.start(MESSAGE)
    accepted(started)
    wait_until(lambda: any(line.get("event", {}).get("type") == "usage" for line in home.events(started.exchange)),
               END_SECONDS, "the interrupted run's usage")
    os.killpg(started.process.pid, signal.SIGTERM)
    started.process.wait(timeout=END_SECONDS)
    check(home.record(started.exchange) is not None, "The interrupted folder disappeared.")
    return started


def run(home: ScenarioHome) -> None:
    unknown = str(uuid.uuid4())
    settled(home.run(["settle", unknown]), unknown, "none")
    equal(home.folders(hidden=True), [], "The unknown settle left nothing")

    home.part("alive")
    live = home.start(MESSAGE)
    accepted(live)
    before = tables(home, live.exchange)["exchanges"]
    refusal(home.run(["settle", live.exchange]), "alive")
    equal(tables(home, live.exchange)["exchanges"], before, "The living Exchange is unchanged")
    check(live.exchange in home.folders(), "Settling removed the living Exchange's folder.")
    os.killpg(live.process.pid, signal.SIGTERM)
    live.process.wait(timeout=END_SECONDS)
    settled(home.run(["settle", live.exchange]), live.exchange, "interrupted")
    snapshot = tables(home, live.exchange)
    settled(home.run(["settle", live.exchange]), live.exchange, "none")
    equal(tables(home, live.exchange), snapshot, "A second settle changes no rows")

    simultaneous = interrupt(home)
    exchange = simultaneous.exchange
    with ThreadPoolExecutor(2) as pool:
        # Hold the table while both command processes enter, without assuming a Trunk's coordination mechanism.
        with home.server.hold(DATABASE, "LOCK TABLE exchanges IN ACCESS EXCLUSIVE MODE"):
            commands = [pool.submit(home.run, ["settle", exchange]) for _ in range(2)]
            time.sleep(0.5)
        results = [command.result(timeout=END_SECONDS) for command in commands]
    for result in results:
        settled(result, exchange, "interrupted")
    check(exchange not in home.folders(hidden=True), "Concurrent settlers left the folder.")
    snapshot = tables(home, exchange)
    equal(snapshot["exchanges"][0]["state"], "interrupted", "The one settled state")
    equal(len(snapshot["runs"]), 1, "Concurrent settling saved one run")
    equal(len(snapshot["tool_calls"]), 1, "Concurrent settling saved one interrupted call")
    settled(home.run(["settle", exchange]), exchange, "none")
    equal(tables(home, exchange), snapshot, "Settling after the concurrent pair changes nothing")
