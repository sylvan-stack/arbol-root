"""R13: settling unknown, live, repeated and concurrent Exchanges, then recovery edges (RCT-2.12)."""

from __future__ import annotations

import json
import os
import shutil
import signal
import time
import uuid
from concurrent.futures import ThreadPoolExecutor
from datetime import UTC, datetime
from typing import Any

from ..home import DATABASE, ROUTE, Completed, ScenarioHome, Started, iso, write_json
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
    check("end" not in home.record(started.exchange), "Termination wrote an end.")
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
    never_accepted(home)
    already_ended(home)
    replaced(home)
    unfinished_line(home)


def never_accepted(home: ScenarioHome) -> None:
    exchange = str(uuid.uuid4())
    file = home.request_file({"route": ROUTE, "message": "not accepted"})
    with home.acceptances_held():
        process = home.spawn(["run", "--detach", "--exchange", exchange, "--request", str(file)])
        record = wait_until(lambda: home.record(exchange), END_SECONDS, "the never-accepted folder")
        check("acceptedAt" not in record, "The abandoned start was accepted.")
        os.killpg(process.pid, signal.SIGKILL)
        process.wait(timeout=END_SECONDS)
    file.unlink(missing_ok=True)
    equal(home.rows(f"SELECT id FROM exchanges WHERE id = '{exchange}'"), [], "The folder has no accepted Exchange")
    settled(home.run(["settle", exchange]), exchange, "none")
    check(exchange not in home.folders(hidden=True), "The never-accepted folder remains.")
    equal(home.rows(f"SELECT id FROM exchanges WHERE id = '{exchange}'"), [], "Settling created no Exchange")


def already_ended(home: ScenarioHome) -> None:
    start = interrupt(home)
    exchange = start.exchange
    saved = home.home / "ended-folder"
    shutil.copytree(home.exchanges_folder / exchange, saved)
    settled(home.run(["settle", exchange]), exchange, "interrupted")
    before = tables(home, exchange)
    shutil.copytree(saved, home.exchanges_folder / exchange)
    record = home.record(exchange)
    record["end"] = {"state": "completed", "at": iso()}
    write_json(home.exchanges_folder / exchange / "record.json", record)
    settled(home.run(["settle", exchange]), exchange, "interrupted")
    equal(tables(home, exchange), before, "The stored end and every saved row stand")


def replaced(home: ScenarioHome) -> None:
    home.part("replace target")
    first = home.start("send again")
    accepted(first)
    exchange = first.exchange
    wait_until(lambda: any(line.get("event", {}).get("type") == "usage" for line in home.events(exchange)),
               END_SECONDS, "the replacement target's recoverable file")
    saved = home.home / "replaced-folder"
    shutil.copytree(home.exchanges_folder / exchange, saved)
    follow = home.follow(exchange)
    try:
        home.release()
        wait_until(lambda: exchange not in home.folders(hidden=True), END_SECONDS, "the target to end")
        first.process.wait(timeout=END_SECONDS)
        finished = next(line["event"] for line in follow.lines() if line.get("event", {}).get("type") == "finished")
    finally:
        follow.close()
    home.part("replacement")
    new = home.start(None, request={"replaces": exchange})
    accepted(new)
    home.release()
    wait_until(lambda: new.exchange not in home.folders(hidden=True), END_SECONDS, "the replacement to end")
    before = tables(home, exchange)
    equal(before["messages"], [], "Replacement deleted the old messages")
    equal(before["tool_calls"], [], "Replacement deleted the old calls")
    shutil.copytree(saved, home.exchanges_folder / exchange)
    # A valid missing small run left in another Build's file must also survive recovery of a replaced Exchange.
    small = {**finished, "runId": exchange + ".recovered-small"}
    lines = home.events(exchange)
    extra = {"n": max(line["n"] for line in lines) + 1, "smallRun": small}
    with (home.exchanges_folder / exchange / "events.jsonl").open("a") as stream:
        stream.write(json.dumps(extra) + "\n")
    settled(home.run(["settle", exchange]), exchange, "completed")
    after = tables(home, exchange)
    equal(after["exchanges"], before["exchanges"], "The replaced Exchange is unchanged")
    equal((after["messages"], after["tool_calls"]), ([], []), "Settling did not restore discarded transcript")
    equal([row for row in after["runs"] if row["run_id"] != small["runId"]], before["runs"], "Existing usage stands")
    recovered = [row for row in after["runs"] if row["run_id"] == small["runId"]]
    equal([(row["kind"], row["usage"]) for row in recovered], [("small", small["usage"])], "Recovered small-run usage")


def unfinished_line(home: ScenarioHome) -> None:
    start = interrupt(home)
    exchange = start.exchange
    lines = home.events(exchange)
    last = next(line["event"]["at"] for line in reversed(lines) if "at" in line.get("event", {}))
    n = max(line["n"] for line in lines) + 1
    tail = {"n": n, "event": {"type": "text", "runId": exchange + ".1", "at": iso(), "text": "unfinished"}}
    with (home.exchanges_folder / exchange / "events.jsonl").open("a") as stream:
        stream.write(json.dumps(tail))
    settled(home.run(["settle", exchange]), exchange, "interrupted")
    equal(home.rows(f"SELECT position FROM messages WHERE exchange_id = '{exchange}' AND position = {n}"), [],
          "The unfinished line was skipped")
    row = home.rows(f"SELECT ended_at FROM exchanges WHERE id = '{exchange}'")[0]
    equal(datetime.fromisoformat(row["ended_at"]).astimezone(UTC).isoformat(),
          datetime.fromisoformat(last).astimezone(UTC).isoformat(), "The end uses the last whole line's time")
