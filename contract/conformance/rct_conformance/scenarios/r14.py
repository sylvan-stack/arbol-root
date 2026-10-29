# Test implementations moved to tests/mid/archived/contract/conformance/rct_conformance/scenarios/r14.py.
"""R14: resend the last message, discard its old transcript and retain its usage (RCT-2.13, 3.4, 3.9)."""

from __future__ import annotations

import uuid
from concurrent.futures import ThreadPoolExecutor
from typing import Any

from ..home import ROUTE, ScenarioHome, Started
from ..judge import check, equal, wait_until
from .r1 import END_SECONDS, accepted
from .r4 import refusal
from .r5 import ended


def finish(home: ScenarioHome, start: Started) -> dict[str, Any]:
    answer = accepted(start)
    ended(home, start, answer["chat"], answer["number"], "completed")
    return answer


def request(home: ScenarioHome, part: str) -> dict[str, Any]:
    records = wait_until(lambda: [r for r in home.received() if r.get("part") == part], END_SECONDS,
                         "the stand-in's " + part + " request")
    value: dict[str, Any] = records[-1]["request"]
    return value


def snapshot(home: ScenarioHome) -> dict[str, Any]:
    return {table: home.rows(f"SELECT * FROM {table} ORDER BY {order}")
            for table, order in (("chats", "id"), ("exchanges", "id"), ("messages", "exchange_id, position"),
                                  ("tool_calls", "exchange_id, position"), ("runs", "exchange_id, run_id"))}


def refused(home: ScenarioHome, target: str, code: str, *, chat: str | None = None,
            message: str | None = None) -> None:
    body: dict[str, Any] = {"route": ROUTE, "replaces": target}
    if chat is not None:
        body["chat"] = chat
    if message is not None:
        body["message"] = message
    file = home.request_file(body)
    before, folders = snapshot(home), home.folders(hidden=True)
    exchange = str(uuid.uuid4())
    try:
        result = home.run(["run", "--detach", "--exchange", exchange, "--request", str(file)])
    finally:
        file.unlink(missing_ok=True)
    refusal(result, code)
    equal(snapshot(home), before, "A refused replacement changes no row")
    equal(home.folders(hidden=True), folders, "A refused replacement leaves no folder")


def run(home: ScenarioHome) -> None:
    raise RuntimeError('Tests are commented under the tier policy; see TESTS.md. Restore only in an explicitly requested testing task.')  # TEST-TIER-REFUSAL


def race(home: ScenarioHome, last: Started, chat: str, *, two_replacements: bool) -> Started:
    home.part("race")
    identifiers = [str(uuid.uuid4()), str(uuid.uuid4())]
    with ThreadPoolExecutor(2) as pool:
        with home.acceptances_held():
            one = pool.submit(home.start, None, exchange=identifiers[0], request={"replaces": last.exchange})
            two = (pool.submit(home.start, None, exchange=identifiers[1], request={"replaces": last.exchange})
                   if two_replacements else pool.submit(home.start, "concurrent next", exchange=identifiers[1],
                                                        request={"chat": chat}))
            wait_until(lambda: all(x in home.folders() for x in identifiers), END_SECONDS, "both pending starts")
        starts = [one.result(timeout=END_SECONDS), two.result(timeout=END_SECONDS)]
    winners = [start for start in starts if start.answer.get("accepted") is True]
    check(len(winners) == 1, "Concurrent replacement accepted the wrong number of Exchanges.", 1, [s.line for s in starts])
    winner = winners[0]
    loser = next(start for start in starts if start is not winner)
    code = "cannot_replace" if two_replacements or winner.exchange == identifiers[1] else "chat_busy"
    equal(loser.answer.get("error", {}).get("code"), code, "The concurrent replacement refusal")
    equal(loser.process.wait(5), 1, "The concurrent replacement refusal's status")
    check(loser.exchange not in home.folders(hidden=True), "The losing replacement left a folder.")
    expected = winner.exchange if two_replacements or winner.exchange == identifiers[0] else None
    equal(home.rows(f"SELECT replaced_by::text FROM exchanges WHERE id = '{last.exchange}'"),
          [{"replaced_by": expected}], "The replacement condition was rechecked atomically")
    home.release()
    finish(home, winner)
    return winner

# Archived complete imports; restore needed names in their original scope, not at this file tail.
