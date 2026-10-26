"""R4: repeats before acceptance, after completion and after an abandoned start (RCT-2.3, 2.18, 2.19)."""

from __future__ import annotations

import os
import signal
import time
import uuid
from concurrent.futures import ThreadPoolExecutor
from typing import Any

from ..home import ROUTE, Completed, ScenarioHome, Started
from ..judge import check, equal, wait_until
from .r1 import END_SECONDS, MESSAGE, accepted
from .r5 import ended


def repeat(home: ScenarioHome, exchange: str) -> Completed:
    file = home.request_file({"route": ROUTE, "message": MESSAGE})
    try:
        return home.run(["run", "--detach", "--exchange", exchange, "--request", str(file)])
    finally:
        file.unlink(missing_ok=True)


def refusal(result: Completed, code: str) -> None:
    equal((result.status, len(result.output)), (1, 1), f"The {code} refusal's status and line count")
    check(result.seconds < 15, "The refusal took more than 15 seconds.", "under 15 seconds", result.seconds)
    equal(result.output[0].get("error", {}).get("code"), code, "The refusal code")


def duplicate(result: Completed, original: dict[str, Any]) -> None:
    equal((result.status, result.output), (0, [{**original, "duplicate": True}]), "The repeated acceptance")
    check(result.seconds < 15, "The repeat took more than 15 seconds.", "under 15 seconds", result.seconds)


def finished(home: ScenarioHome, start: Started) -> dict[str, Any]:
    answer = accepted(start)
    home.release()
    ended(home, start, answer["chat"], answer["number"], "completed")
    return answer


def run(home: ScenarioHome) -> None:
    home.part()
    exchange = str(uuid.uuid4())
    with ThreadPoolExecutor(1) as pool:
        with home.acceptances_held():
            pending = pool.submit(home.start, MESSAGE, exchange=exchange)
            wait_until(lambda: home.record(exchange), END_SECONDS, "the first start's unaccepted folder")
            before = home.record(exchange)
            refusal(repeat(home, exchange), "in_progress")
            equal(home.record(exchange), before, "The first start's preserved record")
            equal(home.rows(f"SELECT id FROM exchanges WHERE id = '{exchange}'"), [], "No accepted row yet")
        first = pending.result(timeout=END_SECONDS)
    original = finished(home, first)
    snapshot = home.rows(f"SELECT * FROM exchanges WHERE id = '{exchange}'")
    duplicate(repeat(home, exchange), original)
    equal(home.rows(f"SELECT * FROM exchanges WHERE id = '{exchange}'"), snapshot, "The ended Exchange on repeat")
    equal(len(home.received()), 1, "The Driver starts after a completed Exchange is repeated")

    home.part("recovered")
    abandoned = str(uuid.uuid4())
    file = home.request_file({"route": ROUTE, "message": "never accepted"})
    with home.acceptances_held():
        process = home.spawn(["run", "--detach", "--exchange", abandoned, "--request", str(file)])
        record = wait_until(lambda: home.record(abandoned), END_SECONDS, "the abandoned start's folder")
        check("acceptedAt" not in record, "The start was accepted before it could be abandoned.")
        os.killpg(process.pid, signal.SIGKILL)
        process.wait(timeout=END_SECONDS)
    file.unlink(missing_ok=True)
    equal(home.rows(f"SELECT id FROM exchanges WHERE id = '{abandoned}'"), [], "The abandoned start has no row")
    refusal(repeat(home, abandoned), "in_progress")
    folder = home.exchanges_folder / abandoned
    info = folder.stat()
    created = getattr(info, "st_birthtime", info.st_mtime)
    wait_until(lambda: time.time() - created >= 15.1, 16, "the abandoned folder to become 15 seconds old")
    recovered = home.start("accepted after abandonment", exchange=abandoned)
    answer = accepted(recovered)
    equal(answer["duplicate"], False, "The reclaimed start is new")
    check(home.record(abandoned)["process"]["pid"] != process.pid, "The abandoned record survived reclamation.")
    finished(home, recovered)
    equal(home.rows(f"SELECT role, text FROM messages WHERE exchange_id = '{abandoned}' AND position = 0"),
          [{"role": "user", "text": "accepted after abandonment"}], "The reclaimed start's new message")
    equal(len([r for r in home.received() if r.get("part") == "recovered"]), 1,
          "Only the reclaimed start reached the Driver")
