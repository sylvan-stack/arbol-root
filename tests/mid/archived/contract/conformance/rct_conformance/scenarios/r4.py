# Mid-tier source from contract/conformance/rct_conformance/scenarios/r4.py; see MID_TIER.md.
# Shared helpers and refusal entry points remain at the original path.

# TEST-TIER-DISABLED-BEGIN contract/conformance/rct_conformance/scenarios/r4.py::run
# def run(home: ScenarioHome) -> None:
#     home.part()
#     exchange = str(uuid.uuid4())
#     with ThreadPoolExecutor(1) as pool:
#         with home.acceptances_held():
#             pending = pool.submit(home.start, MESSAGE, exchange=exchange)
#             wait_until(lambda: home.record(exchange), END_SECONDS, "the first start's unaccepted folder")
#             before = home.record(exchange)
#             refusal(repeat(home, exchange), "in_progress")
#             equal(home.record(exchange), before, "The first start's preserved record")
#             equal(home.rows(f"SELECT id FROM exchanges WHERE id = '{exchange}'"), [], "No accepted row yet")
#         first = pending.result(timeout=END_SECONDS)
#     original = finished(home, first)
#     snapshot = home.rows(f"SELECT * FROM exchanges WHERE id = '{exchange}'")
#     duplicate(repeat(home, exchange), original)
#     equal(home.rows(f"SELECT * FROM exchanges WHERE id = '{exchange}'"), snapshot, "The ended Exchange on repeat")
#     equal(len(home.received()), 1, "The Driver starts after a completed Exchange is repeated")
#
#     home.part("recovered")
#     abandoned = str(uuid.uuid4())
#     file = home.request_file({"route": ROUTE, "message": "never accepted"})
#     with home.acceptances_held():
#         process = home.spawn(["run", "--detach", "--exchange", abandoned, "--request", str(file)])
#         record = wait_until(lambda: home.record(abandoned), END_SECONDS, "the abandoned start's folder")
#         check("acceptedAt" not in record, "The start was accepted before it could be abandoned.")
#         os.killpg(process.pid, signal.SIGKILL)
#         process.wait(timeout=END_SECONDS)
#     file.unlink(missing_ok=True)
#     equal(home.rows(f"SELECT id FROM exchanges WHERE id = '{abandoned}'"), [], "The abandoned start has no row")
#     refusal(repeat(home, abandoned), "in_progress")
#     folder = home.exchanges_folder / abandoned
#     info = folder.stat()
#     created = getattr(info, "st_birthtime", info.st_mtime)
#     wait_until(lambda: time.time() - created >= 15.1, 16, "the abandoned folder to become 15 seconds old")
#     recovered = home.start("accepted after abandonment", exchange=abandoned)
#     answer = accepted(recovered)
#     equal(answer["duplicate"], False, "The reclaimed start is new")
#     check(home.record(abandoned)["process"]["pid"] != process.pid, "The abandoned record survived reclamation.")
#     finished(home, recovered)
#     equal(home.rows(f"SELECT role, text FROM messages WHERE exchange_id = '{abandoned}' AND position = 0"),
#           [{"role": "user", "text": "accepted after abandonment"}], "The reclaimed start's new message")
#     equal(len([r for r in home.received() if r.get("part") == "recovered"]), 1,
#           "Only the reclaimed start reached the Driver")
#     together(home)
#     closed_pipe(home)
# TEST-TIER-DISABLED-END contract/conformance/rct_conformance/scenarios/r4.py::run

# TEST-TIER-IMPORTS-BEGIN contract/conformance/rct_conformance/scenarios/r4.py:5
# import os
# TEST-TIER-IMPORTS-END contract/conformance/rct_conformance/scenarios/r4.py:5

# TEST-TIER-IMPORTS-BEGIN contract/conformance/rct_conformance/scenarios/r4.py:6
# import signal
# TEST-TIER-IMPORTS-END contract/conformance/rct_conformance/scenarios/r4.py:6

# TEST-TIER-IMPORTS-BEGIN contract/conformance/rct_conformance/scenarios/r4.py:7
# import time
# TEST-TIER-IMPORTS-END contract/conformance/rct_conformance/scenarios/r4.py:7

raise RuntimeError("Mid-tier checks require an explicitly requested testing task; see MID_TIER.md.")
