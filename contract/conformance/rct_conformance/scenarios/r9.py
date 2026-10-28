"""R9: an answer to a question (RCT-4).

The stand-in asks the Leather Bag a question, and the suite appends an answer line to `control`, with its fields in an
order of its own. The suite judges: the stand-in got the answer line unchanged, and the run went on; the answer is a
line of `events.jsonl`, exactly as it was in `control`, between the question's `ask_opened` and `ask_closed`; and the
question's row holds the question and the answer.

Covers RCT-1.7 and 1.11.
"""

from __future__ import annotations

from ..home import ScenarioHome

MESSAGE = "Push the branch."
CHOSEN = {"type": "answers", "answers": {"branch": ["main"]}}


# TEST-TIER-DISABLED-BEGIN contract/conformance/rct_conformance/scenarios/r9.py::run
# def run(home: ScenarioHome) -> None:
#     home.part()
#     started = home.start(MESSAGE)
#     accepted(started)
#     exchange = started.exchange
#     follow = home.follow(exchange)
#     try:
#         def asked() -> dict[str, Any] | None:
#             return next((line["event"] for line in home.events(exchange)
#                          if isinstance(line, dict) and line.get("event", {}).get("type") == "ask_opened"), None)
#
#         opened = wait_until(asked, END_SECONDS, "the question")
#         line = {"askId": opened["askId"], "type": "answer", "answer": CHOSEN}  # fields in an order of the suite's own
#         home.control(exchange, line)
#         wait_until(lambda: exchange not in home.folders(hidden=True), END_SECONDS, "the folder to go")
#         lines = follow.lines()
#         raw = follow.data.decode("utf-8").split("\n")
#     finally:
#         follow.close()
#
#     [record] = home.received()
#     equal(record["control"], [line], "The control input of the stand-in")
#     equal(list(record["control"][0]), list(line), "The order of the fields of the answer line the stand-in got")
#     text = json.dumps(line, separators=(",", ":"))  # as home.control wrote it
#     numbered = [n for n, value in enumerate(lines) if isinstance(value, dict) and "answer" in value]
#     check(len(numbered) == 1, "events.jsonl does not hold the answer as one line.", "one answer line",
#           [value for value in lines if isinstance(value, dict) and "answer" in value])
#     at = numbered[0]
#     equal(raw[at], f'{{"n":{at + 1},"answer":{text}}}', "The answer line of events.jsonl")
#     kinds = [value.get("event", {}).get("type") for value in lines]
#     check(kinds.index("ask_opened") < at < kinds.index("ask_closed"),
#           "The answer line is not between the question's ask_opened and ask_closed.", "ask_opened, answer, ask_closed",
#           kinds)
#     check("text" in kinds[at:] and lines[-1].get("end", {}).get("state") == "completed",
#           "The run did not go on to its end after the answer.", "text after the answer, and completed", kinds)
#     equal(home.rows(f"SELECT name, ok, interrupted, ask, answer FROM tool_calls WHERE exchange_id = '{exchange}'"),
#           [{"name": "ask_user", "ok": True, "interrupted": False, "ask": opened["ask"], "answer": CHOSEN}],
#           "The row of the question")
#     equal(home.rows(f"SELECT state FROM exchanges WHERE id = '{exchange}'"), [{"state": "completed"}], "The Exchange")
# TEST-TIER-DISABLED-END contract/conformance/rct_conformance/scenarios/r9.py::run
def run(home: ScenarioHome) -> None:
    raise RuntimeError('Tests are commented under the tier policy; see TESTS.md. Restore only in an explicitly requested testing task.')  # TEST-TIER-REFUSAL

# Archived complete imports; restore needed names in their original scope, not at this file tail.
# TEST-TIER-IMPORTS-BEGIN contract/conformance/rct_conformance/scenarios/r9.py:13
# import json
# TEST-TIER-IMPORTS-END contract/conformance/rct_conformance/scenarios/r9.py:13
# TEST-TIER-IMPORTS-BEGIN contract/conformance/rct_conformance/scenarios/r9.py:14
# from typing import Any
# TEST-TIER-IMPORTS-END contract/conformance/rct_conformance/scenarios/r9.py:14
# TEST-TIER-IMPORTS-BEGIN contract/conformance/rct_conformance/scenarios/r9.py:17
# from ..judge import check, equal, wait_until
# TEST-TIER-IMPORTS-END contract/conformance/rct_conformance/scenarios/r9.py:17
# TEST-TIER-IMPORTS-BEGIN contract/conformance/rct_conformance/scenarios/r9.py:18
# from .r1 import END_SECONDS, accepted
# TEST-TIER-IMPORTS-END contract/conformance/rct_conformance/scenarios/r9.py:18
