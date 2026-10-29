# Mid-tier source from contract/conformance/rct_conformance/scenarios/r5.py; see MID_TIER.md.
# Shared helpers and refusal entry points remain at the original path.

# TEST-TIER-DISABLED-BEGIN contract/conformance/rct_conformance/scenarios/r5.py::run
# def run(home: ScenarioHome) -> None:
#     home.part()
#     first = home.start(MESSAGE)
#     chat = accepted(first)["chat"]
#     ended(home, first, chat, 1, "completed")
#
#     # A second message with --chat, while the request file names another chat and the route's model.
#     home.part()
#     second = home.start("And the tests?", request={"chat": str(uuid.uuid4()), "route": dict(ROUTE)},
#                         options=("--chat", chat, "--model", OTHER_MODEL))
#     ended(home, second, chat, 2, "completed")
#     equal(home.rows(f"SELECT route FROM exchanges WHERE id = '{second.exchange}'"),
#           [{"route": {**ROUTE, "model": OTHER_MODEL}}], "The route of the second message")
#     equal(standin_request(home, "", 1).get("model"), OTHER_MODEL, "The model the stand-in was asked for")
#
#     home.part("fails")
#     ended(home, home.start("Run them.", request={"chat": chat}), chat, 3, "failed")
#     home.part()
#     ended(home, home.start("Once more, after the failure.", request={"chat": chat}), chat, 4, "completed")
#
#     home.part("stopped")
#     stopped = home.start("Build it.", request={"chat": chat})
#     accepted(stopped)
#     wait_until(lambda: home.events(stopped.exchange), END_SECONDS, "the first event of the Exchange to stop")
#     home.control(stopped.exchange, {"type": "stop"})
#     ended(home, stopped, chat, 5, "cancelled")
#
#     # After a cancelled Exchange, and without --cwd: the working folder is the folder the Trunk was started from.
#     home.part()
#     elsewhere = home.home / "elsewhere"
#     elsewhere.mkdir()
#     after = home.start("Once more, after the stop.", request={"chat": chat}, cwd=elsewhere)
#     ended(home, after, chat, 6, "completed")
#     folder = str(elsewhere.resolve())
#     equal(home.rows(f"SELECT working_folder FROM exchanges WHERE id = '{after.exchange}'"),
#           [{"working_folder": folder}], "The working folder of a message without --cwd")
#     record = home.received()[-1]
#     equal([record["workingDirectory"], record["request"].get("workingDirectory")], [folder, folder],
#           "Where the stand-in was started, and the working folder its request names")
#
#     together(home, chat)
#     equal(home.rows(f"SELECT number, state FROM exchanges WHERE chat_id = '{chat}' ORDER BY number"),
#           [{"number": n, "state": state} for n, state in enumerate(
#               ["completed", "completed", "failed", "completed", "cancelled", "completed", "completed"], 1)],
#           "The Exchanges of the chat")
# TEST-TIER-DISABLED-END contract/conformance/rct_conformance/scenarios/r5.py::run

# TEST-TIER-IMPORTS-BEGIN contract/conformance/rct_conformance/scenarios/r5.py:15
# import uuid
# TEST-TIER-IMPORTS-END contract/conformance/rct_conformance/scenarios/r5.py:15

# TEST-TIER-IMPORTS-BEGIN contract/conformance/rct_conformance/scenarios/r5.py:19
# from ..home import ROUTE, ScenarioHome, Started
# TEST-TIER-IMPORTS-END contract/conformance/rct_conformance/scenarios/r5.py:19

raise RuntimeError("Mid-tier checks require an explicitly requested testing task; see MID_TIER.md.")
