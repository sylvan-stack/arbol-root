# Mid-tier source from contract/conformance/rct_conformance/scenarios/r1.py; see MID_TIER.md.
# Shared helpers and refusal entry points remain at the original path.

# TEST-TIER-DISABLED-BEGIN contract/conformance/rct_conformance/scenarios/r1.py::run
# def run(home: ScenarioHome) -> None:
#     home.part()
#     started = home.start(MESSAGE)
#     answer = accepted(started)
#     exchange, chat = started.exchange, answer["chat"]
#     equal(answer["number"], 1, "The number of the chat's first Exchange")
#
#     # When the line came, the folder, the chat, the open Exchange and the message at position 0 were there.
#     check(exchange in home.folders(), "The Exchange has no folder once it is accepted.", exchange, home.folders())
#     follow = home.follow(exchange)
#     try:
#         record = home.record(exchange)
#         check(isinstance(record, dict) and "acceptedAt" in record, "The record has no acceptedAt once accepted.",
#               "acceptedAt", record)
#         equal({name: record.get(name) for name in ("rootContract", "root", "exchange", "chat", "trunk", "build",
#                                                     "route", "workingFolder")},
#               {"rootContract": home.root_contract, "root": ROOT, "exchange": exchange, "chat": chat,
#                "trunk": answer["trunk"], "build": answer["build"], "route": ROUTE,
#                "workingFolder": str(home.work.resolve())}, "The record of the accepted Exchange")
#         equal(record["process"]["pid"], started.process.pid, "The record's process")
#         equal(home.rows(f"SELECT id::text FROM chats WHERE id = '{chat}'"), [{"id": chat}], "The chat")
#         equal(home.rows(f"SELECT number, state, trunk, build, route FROM exchanges WHERE id = '{exchange}'"),
#               [{"number": 1, "state": "open", "trunk": answer["trunk"], "build": answer["build"], "route": ROUTE}],
#               "The open Exchange")
#         equal(home.rows(f"SELECT position, role, text FROM messages WHERE exchange_id = '{exchange}'"),
#               [{"position": 0, "role": "user", "text": MESSAGE}], "The message at position 0")
#         check(started.process.poll() is None, "The Trunk did not live on after the suite closed its end of the pipe.")
#
#         wait_until(lambda: exchange not in home.folders(hidden=True), END_SECONDS, "the Exchange's folder to go")
#         received = home.received()
#         equal(len(received), 1, "The starts of the stand-in")
#         check(received[0]["launcher"] == "arbol-claude-driver" and received[0]["arguments"][:1] == ["run"]
#               and "--control" in received[0]["arguments"],
#               "The stand-in was not started through its launcher name as run with --control.",
#               ["arbol-claude-driver", "run", "--control"], [received[0]["launcher"], received[0]["arguments"]])
#         lines = follow.lines()
#     finally:
#         follow.close()
#
#     # n from 1 without gaps, every event as the stand-in wrote it, the end last.
#     equal([line.get("n") if isinstance(line, dict) else line for line in lines], list(range(1, len(lines) + 1)),
#           "The n of the lines of events.jsonl")
#     written = [json.loads(event) for event in received[0]["events"]]
#     equal([line.get("event") for line in lines[:-1]], written, "The events in events.jsonl")
#     end = lines[-1].get("end")
#     check(isinstance(end, dict) and end.get("state") == "completed" and "error" not in end,
#           "The last line of events.jsonl is not a completed end.", "completed", lines[-1])
#     judge_rows(home, exchange, written)
# TEST-TIER-DISABLED-END contract/conformance/rct_conformance/scenarios/r1.py::run

# TEST-TIER-IMPORTS-BEGIN contract/conformance/rct_conformance/scenarios/r1.py:14
# import json
# TEST-TIER-IMPORTS-END contract/conformance/rct_conformance/scenarios/r1.py:14

# TEST-TIER-IMPORTS-BEGIN contract/conformance/rct_conformance/scenarios/r1.py:19
# from ..home import ROOT, ROUTE, ScenarioHome, Started
# TEST-TIER-IMPORTS-END contract/conformance/rct_conformance/scenarios/r1.py:19

# TEST-TIER-IMPORTS-BEGIN contract/conformance/rct_conformance/scenarios/r1.py:20
# from ..judge import check, equal, wait_until
# TEST-TIER-IMPORTS-END contract/conformance/rct_conformance/scenarios/r1.py:20

raise RuntimeError("Mid-tier checks require an explicitly requested testing task; see MID_TIER.md.")
