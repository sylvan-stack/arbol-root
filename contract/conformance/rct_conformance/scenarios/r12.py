"""R12: lose PostgreSQL during work and after acceptance; recover both before and after the end."""

from __future__ import annotations

from ..home import ScenarioHome
from ..judge import equal, wait_until
from .r1 import END_SECONDS, accepted


def run(home: ScenarioHome) -> None:
    during_work(home)


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
