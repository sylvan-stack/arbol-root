"""R14: resend the last message, discard its old transcript and retain its usage (RCT-2.13, 3.4, 3.9)."""

from __future__ import annotations

import json
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
    home.part("earlier")
    earlier = home.start("earlier message")
    chat = finish(home, earlier)["chat"]
    home.part("original")
    first = home.start("send this again", request={"chat": chat})
    first_answer = finish(home, first)
    original_request = request(home, "original")
    old = home.rows(f"SELECT * FROM exchanges WHERE id = '{first.exchange}'")[0]
    old_runs = home.rows(f"SELECT * FROM runs WHERE exchange_id = '{first.exchange}' ORDER BY run_id")
    check(old_runs, "The original Exchange has no usage to preserve.")

    home.part("replacement")
    second = home.start(None, request={"replaces": first.exchange})
    answer = finish(home, second)
    equal((answer["chat"], answer["number"]), (chat, first_answer["number"] + 1), "The replacement's chat and number")
    equal(home.rows(f"SELECT text FROM messages WHERE exchange_id = '{second.exchange}' AND position = 0"),
          [{"text": "send this again"}], "The copied message")
    equal(home.rows(f"SELECT * FROM exchanges WHERE id = '{first.exchange}'"), [{**old, "replaced_by": second.exchange}],
          "Only replaced_by changed in the old Exchange")
    equal(home.rows(f"SELECT * FROM messages WHERE exchange_id = '{first.exchange}'"), [], "Old messages deleted")
    equal(home.rows(f"SELECT * FROM tool_calls WHERE exchange_id = '{first.exchange}'"), [], "Old calls deleted")
    equal(home.rows(f"SELECT * FROM runs WHERE exchange_id = '{first.exchange}' ORDER BY run_id"), old_runs,
          "Old usage preserved")
    new_request = request(home, "replacement")
    equal(new_request["input"], original_request["input"], "The replacement's Driver input")
    equal(new_request["history"], original_request["history"], "The history after the old answer is discarded")
    check(new_request["history"], "The replacement discarded earlier Exchanges too.")

    home.part("next")
    next_message = home.start("a next message", request={"chat": chat})
    finish(home, next_message)
    following = request(home, "next")["history"]
    equal(following[:len(new_request["history"])], new_request["history"], "Earlier history remains")
    check("original answer" not in json.dumps(following) and "echo original" not in json.dumps(following),
          "The next request contains the replaced answer or tool call.")
    check("replacement answer" in json.dumps(following) and "echo replacement" in json.dumps(following),
          "The next request lost the new answer or tool call.")
    refused(home, earlier.exchange, "cannot_replace")
    refused(home, first.exchange, "cannot_replace")
    refused(home, next_message.exchange, "invalid_input", chat=str(uuid.uuid4()))
    refused(home, next_message.exchange, "invalid_input", message="an edited message")
    refused(home, str(uuid.uuid4()), "not_found")

    last = race(home, next_message, chat, two_replacements=False)
    last = race(home, last, chat, two_replacements=True)
    home.part("open")
    opened = home.start("still open", request={"chat": chat})
    accepted(opened)
    refused(home, opened.exchange, "cannot_replace")
    home.release()
    finish(home, opened)


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
