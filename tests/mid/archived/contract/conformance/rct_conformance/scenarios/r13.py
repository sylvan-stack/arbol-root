# Mid-tier source from contract/conformance/rct_conformance/scenarios/r13.py; see MID_TIER.md.
# Shared helpers and refusal entry points remain at the original path.

# TEST-TIER-DISABLED-BEGIN contract/conformance/rct_conformance/scenarios/r13.py::run
# def run(home: ScenarioHome) -> None:
#     unknown = str(uuid.uuid4())
#     settled(home.run(["settle", unknown]), unknown, "none")
#     equal(home.folders(hidden=True), [], "The unknown settle left nothing")
#
#     home.part("alive")
#     live = home.start(MESSAGE)
#     accepted(live)
#     before = tables(home, live.exchange)["exchanges"]
#     refusal(home.run(["settle", live.exchange]), "alive")
#     equal(tables(home, live.exchange)["exchanges"], before, "The living Exchange is unchanged")
#     check(live.exchange in home.folders(), "Settling removed the living Exchange's folder.")
#     os.killpg(live.process.pid, signal.SIGTERM)
#     live.process.wait(timeout=END_SECONDS)
#     settled(home.run(["settle", live.exchange]), live.exchange, "interrupted")
#     snapshot = tables(home, live.exchange)
#     settled(home.run(["settle", live.exchange]), live.exchange, "none")
#     equal(tables(home, live.exchange), snapshot, "A second settle changes no rows")
#
#     simultaneous = interrupt(home)
#     exchange = simultaneous.exchange
#     with ThreadPoolExecutor(2) as pool:
#         # Hold the table while both command processes enter, without assuming a Trunk's coordination mechanism.
#         with home.server.hold(DATABASE, "LOCK TABLE exchanges IN ACCESS EXCLUSIVE MODE"):
#             commands = [pool.submit(home.run, ["settle", exchange]) for _ in range(2)]
#             time.sleep(0.5)
#         results = [command.result(timeout=END_SECONDS) for command in commands]
#     for result in results:
#         settled(result, exchange, "interrupted")
#     check(exchange not in home.folders(hidden=True), "Concurrent settlers left the folder.")
#     snapshot = tables(home, exchange)
#     equal(snapshot["exchanges"][0]["state"], "interrupted", "The one settled state")
#     equal(len(snapshot["runs"]), 1, "Concurrent settling saved one run")
#     equal(len(snapshot["tool_calls"]), 1, "Concurrent settling saved one interrupted call")
#     settled(home.run(["settle", exchange]), exchange, "none")
#     equal(tables(home, exchange), snapshot, "Settling after the concurrent pair changes nothing")
#     never_accepted(home)
#     already_ended(home)
#     replaced(home)
#     unfinished_line(home)
# TEST-TIER-DISABLED-END contract/conformance/rct_conformance/scenarios/r13.py::run

# TEST-TIER-IMPORTS-BEGIN contract/conformance/rct_conformance/scenarios/r13.py:9
# import time
# TEST-TIER-IMPORTS-END contract/conformance/rct_conformance/scenarios/r13.py:9

# TEST-TIER-IMPORTS-BEGIN contract/conformance/rct_conformance/scenarios/r13.py:11
# from concurrent.futures import ThreadPoolExecutor
# TEST-TIER-IMPORTS-END contract/conformance/rct_conformance/scenarios/r13.py:11

# TEST-TIER-IMPORTS-BEGIN contract/conformance/rct_conformance/scenarios/r13.py:15
# from ..home import DATABASE, ROUTE, Completed, ScenarioHome, Started, iso, write_json
# TEST-TIER-IMPORTS-END contract/conformance/rct_conformance/scenarios/r13.py:15

# TEST-TIER-IMPORTS-BEGIN contract/conformance/rct_conformance/scenarios/r13.py:18
# from .r4 import refusal
# TEST-TIER-IMPORTS-END contract/conformance/rct_conformance/scenarios/r13.py:18

raise RuntimeError("Mid-tier checks require an explicitly requested testing task; see MID_TIER.md.")
