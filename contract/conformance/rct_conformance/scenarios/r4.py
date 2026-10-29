# Test implementations moved to tests/mid/archived/contract/conformance/rct_conformance/scenarios/r4.py.
"""R4: repeats before acceptance, after completion and after an abandoned start (RCT-2.3, 2.18, 2.19)."""

from __future__ import annotations

import uuid
from concurrent.futures import FIRST_COMPLETED, ThreadPoolExecutor, wait
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
    raise RuntimeError('Tests are commented under the tier policy; see TESTS.md. Restore only in an explicitly requested testing task.')  # TEST-TIER-REFUSAL


def together(home: ScenarioHome) -> None:
    home.part("together")
    exchange = str(uuid.uuid4())
    with ThreadPoolExecutor(2) as pool:
        with home.acceptances_held():
            futures = [pool.submit(home.start, text, exchange=exchange) for text in ("first", "second")]
            done, pending = wait(futures, timeout=END_SECONDS, return_when=FIRST_COMPLETED)
            check(len(done) == len(pending) == 1, "Two simultaneous starts did not leave one acceptance pending.")
            loser = next(iter(done)).result()
            equal(loser.answer.get("error", {}).get("code"), "in_progress", "The simultaneous start's refusal")
            equal(loser.process.wait(5), 1, "The simultaneous start's refusal status")
            check(loser.seconds < 15, "The simultaneous-start refusal was late.")
            equal(home.folders(hidden=True), [exchange], "The winner's one folder")
            equal(home.rows(f"SELECT id FROM exchanges WHERE id = '{exchange}'"), [], "The pending acceptance")
        winner = next(iter(pending)).result(timeout=END_SECONDS)
    finished(home, winner)
    equal(len(home.rows(f"SELECT id FROM exchanges WHERE id = '{exchange}'")), 1, "The one accepted Exchange")
    equal(len([r for r in home.received() if r.get("part") == "together"]), 1,
          "The Driver starts for simultaneous submissions")


def closed_pipe(home: ScenarioHome) -> None:
    home.part("closed pipe")
    exchange = str(uuid.uuid4())
    file = home.request_file({"route": ROUTE, "message": MESSAGE})
    process = home.spawn(["run", "--detach", "--exchange", exchange, "--request", str(file)])
    assert process.stdout is not None
    process.stdout.close()  # the starter disappears without reading even the acceptance line
    rows = wait_until(lambda: home.rows("SELECT id::text, chat_id::text, number, trunk, build"
                                       f" FROM exchanges WHERE id = '{exchange}'"), END_SECONDS,
                      "the acceptance whose pipe was closed")
    stored = rows[0]
    expected = {"accepted": True, "duplicate": False, "root": "rct", "exchange": exchange,
                "chat": stored["chat_id"], "number": stored["number"], "trunk": stored["trunk"], "build": stored["build"]}
    duplicate(repeat(home, exchange), expected)
    home.release()
    wait_until(lambda: exchange not in home.folders(hidden=True), END_SECONDS, "the closed-pipe Exchange to finish")
    equal(process.wait(5), 0, "The closed-pipe start's exit status")
    equal(home.rows(f"SELECT state FROM exchanges WHERE id = '{exchange}'"), [{"state": "completed"}],
          "The closed-pipe Exchange's state")
    equal(len([r for r in home.received() if r.get("part") == "closed pipe"]), 1,
          "The Driver starts after losing and repeating an acceptance")
    file.unlink(missing_ok=True)

# Archived complete imports; restore needed names in their original scope, not at this file tail.
