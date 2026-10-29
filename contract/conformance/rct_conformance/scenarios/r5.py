# Test implementations moved to tests/mid/archived/contract/conformance/rct_conformance/scenarios/r5.py.
"""R5: a chat goes on (RCT-4).

A second message with `--chat`, a message after a failed and after a cancelled Exchange, a message without `--cwd`,
and two messages to one chat at the same moment. The suite judges: the numbers 2, 3 and on; each accepted; the working
folder is the folder the suite started the Trunk from; of the two at the same moment one is accepted and the other
refused with `chat_busy`. The second message also names, in its request file, another chat and the route's model, and
`--chat` and `--model` replace only their own fields (RCT-0.4).

Covers RCT-0.4, 0.5 and 2.17.
"""

from __future__ import annotations

import subprocess
from concurrent.futures import ThreadPoolExecutor
from typing import Any

from ..home import ScenarioHome, Started
from ..judge import check, equal, wait_until
from .r1 import END_SECONDS, accepted

MESSAGE = "What does build.sh do?"
OTHER_MODEL = "standin-other-model"
EXIT_SECONDS = 5.0


def run(home: ScenarioHome) -> None:
    raise RuntimeError('Tests are commented under the tier policy; see TESTS.md. Restore only in an explicitly requested testing task.')  # TEST-TIER-REFUSAL


def together(home: ScenarioHome, chat: str) -> None:
    """Two messages to one chat at the same moment: one is accepted, the other refused with `chat_busy`, naming the
    accepted one, and leaves no folder; the accepted one's run is held open until both have answered."""
    home.part("together")
    with ThreadPoolExecutor(2) as pool:
        starts = list(pool.map(lambda text: home.start(text, request={"chat": chat}),
                               ["The first of two.", "The second of two."]))
    taken = [start for start in starts if isinstance(start.answer, dict) and start.answer.get("accepted") is True]
    busy = [start for start in starts if start not in taken]
    check(len(taken) == 1 and len(busy) == 1, "Of two messages at the same moment, not exactly one was accepted.",
          "one accepted and one refused", [start.line for start in starts])
    error = busy[0].answer.get("error") if isinstance(busy[0].answer, dict) else None
    check(isinstance(error, dict) and error.get("code") == "chat_busy",
          "The other message at the same moment was not refused with chat_busy.", "chat_busy", busy[0].line)
    assert isinstance(error, dict)
    check(taken[0].exchange in str(error.get("message")), "The refusal does not name the accepted Exchange.",
          taken[0].exchange, error.get("message"))
    equal(exit_status(busy[0]), 1, "The exit status of the refused message")
    check(busy[0].exchange not in home.folders(hidden=True), "The refused message left a folder.")
    home.release()
    ended(home, taken[0], chat, 7, "completed")
    equal(len([record for record in home.received() if record.get("part") == "together"]), 1,
          "The starts of the stand-in for the two messages")


def ended(home: ScenarioHome, started: Started, chat: str, number: int, state: str) -> None:
    """The start was accepted in the chat with the number, and its Exchange ended with the state."""
    answer = accepted(started)
    equal([answer["chat"], answer["number"]], [chat, number], f"The chat and the number of message {number}")
    wait_until(lambda: started.exchange not in home.folders(hidden=True), END_SECONDS,
               f"the folder of message {number} to go")
    equal(home.rows(f"SELECT state FROM exchanges WHERE id = '{started.exchange}'"), [{"state": state}],
          f"The state of message {number}")


def standin_request(home: ScenarioHome, part: str, index: int) -> Any:
    """The request of the stand-in's start number `index` (from 0) in the part."""
    records = [record for record in home.received() if record.get("part") == part]
    return records[index]["request"]


def exit_status(started: Started) -> int | None:
    try:
        return started.process.wait(EXIT_SECONDS)
    except subprocess.TimeoutExpired:
        return None

# Archived complete imports; restore needed names in their original scope, not at this file tail.
