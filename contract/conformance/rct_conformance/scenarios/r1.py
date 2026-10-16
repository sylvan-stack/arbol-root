"""R1: a plain answer in the background (RCT-4).

The stand-in writes text, a `shell` call, more text and usage, and completes. The suite judges: one acceptance line,
and when it came the folder, the chat, the open Exchange and the message at position 0 were there; the process lived on
after the suite closed its end of the pipe; the stand-in was started through its launcher name with `--control`; `n`
from 1 without gaps, every event as the stand-in wrote it, the end last; the rows at their positions, the run of the kind
`agent` with its usage and its `started` event; the Exchange completed; the folder gone.

Covers RCT-0.4, 0.6, 0.14, 1.1, 1.2, 1.5, 2.1, 2.4, 2.9, 2.20, 3.1, 3.2 and 3.3.
"""

from __future__ import annotations

import re
from typing import Any

from ..home import ROOT, ROUTE, ScenarioHome, Started
from ..judge import check, equal, wait_until

MESSAGE = "What does build.sh do?"
CODE_NAME = re.compile(r"[a-z][a-z0-9]{0,31}")
BUILD = re.compile(r"0|[1-9a-f][0-9a-f]*")
ACCEPTANCE_SECONDS = 15.0
END_SECONDS = 30.0


def accepted(started: Started) -> dict[str, Any]:
    """The one acceptance line of a start, judged as RCT-2's Accepted."""
    check(isinstance(started.answer, dict) and started.answer.get("accepted") is True,
          "The Trunk did not accept the message.", "an acceptance line", started.line)
    answer: dict[str, Any] = started.answer
    check(started.seconds < ACCEPTANCE_SECONDS, f"The answer came after {started.seconds:.1f} s.",
          f"within {ACCEPTANCE_SECONDS:g} s", started.seconds)
    equal(sorted(answer), sorted(["accepted", "duplicate", "root", "exchange", "chat", "number", "trunk", "build"]),
          "The fields of the acceptance line")
    equal([answer["duplicate"], answer["root"], answer["exchange"]], [False, ROOT, started.exchange],
          "duplicate, root and exchange of the acceptance line")
    check(isinstance(answer["trunk"], str) and CODE_NAME.fullmatch(answer["trunk"]), "trunk is no code name.",
          "a code name", answer["trunk"])
    check(isinstance(answer["build"], str) and BUILD.fullmatch(answer["build"]), "build is no build number.",
          "a build number", answer["build"])
    return answer


def run(home: ScenarioHome) -> None:
    home.part()
    started = home.start(MESSAGE)
    answer = accepted(started)
    exchange, chat = started.exchange, answer["chat"]
    equal(answer["number"], 1, "The number of the chat's first Exchange")

    # When the line came, the folder, the chat, the open Exchange and the message at position 0 were there.
    check(exchange in home.folders(), "The Exchange has no folder once it is accepted.", exchange, home.folders())
    follow = home.follow(exchange)
    try:
        record = home.record(exchange)
        check(isinstance(record, dict) and "acceptedAt" in record, "The record has no acceptedAt once accepted.",
              "acceptedAt", record)
        equal({name: record.get(name) for name in ("rootContract", "root", "exchange", "chat", "trunk", "build",
                                                    "route", "workingFolder")},
              {"rootContract": home.root_contract, "root": ROOT, "exchange": exchange, "chat": chat,
               "trunk": answer["trunk"], "build": answer["build"], "route": ROUTE,
               "workingFolder": str(home.work.resolve())}, "The record of the accepted Exchange")
        equal(record["process"]["pid"], started.process.pid, "The record's process")
        equal(home.rows(f"SELECT id::text FROM chats WHERE id = '{chat}'"), [{"id": chat}], "The chat")
        equal(home.rows(f"SELECT number, state, trunk, build, route FROM exchanges WHERE id = '{exchange}'"),
              [{"number": 1, "state": "open", "trunk": answer["trunk"], "build": answer["build"], "route": ROUTE}],
              "The open Exchange")
        equal(home.rows(f"SELECT position, role, text FROM messages WHERE exchange_id = '{exchange}'"),
              [{"position": 0, "role": "user", "text": MESSAGE}], "The message at position 0")
        check(started.process.poll() is None, "The Trunk did not live on after the suite closed its end of the pipe.")

        wait_until(lambda: exchange not in home.folders(hidden=True), END_SECONDS, "the Exchange's folder to go")
        received = home.received()
        equal(len(received), 1, "The starts of the stand-in")
        check(received[0]["launcher"] == "arbol-claude-driver" and received[0]["arguments"][:1] == ["run"]
              and "--control" in received[0]["arguments"],
              "The stand-in was not started through its launcher name as run with --control.",
              ["arbol-claude-driver", "run", "--control"], [received[0]["launcher"], received[0]["arguments"]])
    finally:
        follow.close()
