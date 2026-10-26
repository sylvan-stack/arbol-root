"""R12: lose PostgreSQL during work and after acceptance; recover both before and after the end."""

from __future__ import annotations

import time

from ..home import TIME_SCALE, ScenarioHome
from ..judge import check, equal, wait_until
from .r1 import END_SECONDS, accepted
from .r13 import settled, tables


def run(home: ScenarioHome) -> None:
    during_work(home)
    after_acceptance(home)
    through_the_end(home)


def during_work(home: ScenarioHome) -> None:
    home.part("middle")
    started = home.start()
    accepted(started)
    exchange = started.exchange
    wait_until(lambda: home.rows(f"SELECT text FROM messages WHERE exchange_id = '{exchange}' AND position > 0"),
               END_SECONDS, "the first saved block")
    home.server.stop()
    home.release()
    wait_until(lambda: any(line.get("event", {}).get("type") == "usage" for line in home.events(exchange)),
               END_SECONDS, "the answer to continue in the file while PostgreSQL is away")
    equal(started.process.poll(), None, "The Trunk keeps working while the database is away")
    home.server.start()
    wait_until(lambda: len(home.rows(f"SELECT text FROM messages WHERE exchange_id = '{exchange}' AND position > 0")) == 2,
               END_SECONDS, "the unsaved blocks to be retried before the run ends")
    wait_until(lambda: home.rows(f"SELECT name FROM tool_calls WHERE exchange_id = '{exchange}'"),
               END_SECONDS, "the unsaved tool call to be retried")
    (home.standin / "finish").write_text("\n")
    equal(started.process.wait(timeout=END_SECONDS), 0, "The recovered Trunk's exit status")
    judge_saved(home, exchange)
    equal(home.folders(hidden=True), [], "The recovered folder was removed")


def judge_saved(home: ScenarioHome, exchange: str) -> None:
    equal(home.rows(f"SELECT text FROM messages WHERE exchange_id = '{exchange}' AND position > 0 ORDER BY position"),
          [{"text": "Before the database went away."}, {"text": "Written while the database was away."}],
          "Both blocks were saved in order")
    equal(home.rows(f"SELECT name, result FROM tool_calls WHERE exchange_id = '{exchange}'"),
          [{"name": "shell", "result": {"output": "#!/bin/sh\nset -e\n", "exitCode": 0}}], "The saved call")
    equal(home.rows(f"SELECT outcome, usage FROM runs WHERE exchange_id = '{exchange}'"),
          [{"outcome": "completed", "usage": {"model": "standin-model", "inputTokens": 31, "outputTokens": 9}}],
          "The saved run and its usage")
    equal(home.rows(f"SELECT state, error FROM exchanges WHERE id = '{exchange}'"),
          [{"state": "completed", "error": None}], "The saved end")


def after_acceptance(home: ScenarioHome) -> None:
    home.part("acceptance")
    started = home.start()
    accepted(started)
    exchange = started.exchange
    home.server.stop()
    time.sleep(61 / TIME_SCALE)
    home.server.start()
    home.release()
    status = started.process.wait(timeout=END_SECONDS)
    row = home.rows(f"SELECT state, error FROM exchanges WHERE id = '{exchange}'")[0]
    if row["state"] == "failed":
        equal((status, row["error"]["code"]), (1, "database_unavailable"),
              "A Trunk needing history fails truthfully after its read budget")
    else:
        equal(status, 0, "A Trunk needing no more history completes")
        judge_saved(home, exchange)
    check(exchange not in home.folders(hidden=True), "Recovery after acceptance left the folder.")


def through_the_end(home: ScenarioHome) -> None:
    home.part("end")
    started = home.start()
    accepted(started)
    exchange = started.exchange
    wait_until(lambda: any(line.get("event", {}).get("type") == "text" for line in home.events(exchange)),
               END_SECONDS, "the Driver to be running before the final outage")
    home.server.stop()
    before = home.record(exchange)["signsOfLife"]["heartbeat"]
    time.sleep(61 / TIME_SCALE)
    equal(started.process.poll(), None, "The Driver remains working after 60 seconds without PostgreSQL")
    check(home.record(exchange)["signsOfLife"]["heartbeat"] > before,
          "The work loop stopped raising signs of life while PostgreSQL was away.")
    home.release()
    wait_until(lambda: home.record(exchange).get("end"), END_SECONDS, "the end to reach the record without PostgreSQL")
    began = time.monotonic()
    equal(started.process.wait(timeout=END_SECONDS), 0, "The Trunk ends after its bounded final tries")
    check(time.monotonic() - began < 60 / TIME_SCALE + 6, "The final database tries exceeded their budget.")
    check(exchange in home.folders(), "The unsaved Exchange lost its recovery folder.")
    record = home.record(exchange)
    lines = home.events(exchange)
    equal(lines[-1]["end"], record["end"], "The end is recoverable from both file and record")
    equal(record["end"]["state"], "completed", "A Trunk needing no further history can complete without PostgreSQL")
    check(any(line.get("event", {}).get("type") == "usage" for line in lines),
          "The Driver's later output was lost while PostgreSQL was away.")
    home.server.start()
    settled(home.run(["settle", exchange]), exchange, "completed")
    judge_saved(home, exchange)
    check(exchange not in home.folders(hidden=True), "Settling left the recovered folder.")
    before_tables = tables(home, exchange)
    settled(home.run(["settle", exchange]), exchange, "none")
    equal(tables(home, exchange), before_tables, "Repeated settling changes no recovered row")
