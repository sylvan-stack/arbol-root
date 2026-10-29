# Mid-tier source from contract/conformance/rct_conformance/scenarios/r17.py; see MID_TIER.md.
# Shared helpers and refusal entry points remain at the original path.

# TEST-TIER-DISABLED-BEGIN contract/conformance/rct_conformance/scenarios/r17.py::run
# def run(home: ScenarioHome) -> None:
#     home.part()
#     started = home.start(MESSAGE, request={"route": {**ROUTE, "model": MODEL},
#                                           "smallCallRoute": {"driver": "codex", "model": MODEL}})
#     accepted(started)
#     exchange = started.exchange
#     follow = home.follow(exchange)
#     try:
#         home.release()
#         equal(started.process.wait(timeout=END_SECONDS), 0, "The character scenario completes")
#         lines = follow.lines()
#     finally:
#         follow.close()
#     records = home.received()
#     equal(len(records), 1, "One Driver run")
#     equal(records[0]["request"]["input"]["text"], MESSAGE, "The Driver gets the original message")
#     written = [json.loads(raw) for raw in records[0]["events"]]
#     equal([line["event"] for line in lines[:-1]], written, "The file preserves every original event value")
#     raw_lines = follow.data.decode("utf-8").splitlines()
#     equal(raw_lines[:-1], [f'{{"n":{n},"event":{raw}}}' for n, raw in enumerate(records[0]["events"], 1)],
#           "The file preserves the exact event JSON")
#     equal(lines[-1]["end"]["state"], "completed", "The file's end")
#     equal(home.rows(f"SELECT role, text FROM messages WHERE exchange_id = '{exchange}' ORDER BY position"),
#           [{"role": "user", "text": STORED_MESSAGE}, {"role": "assistant", "text": "A whole 😀 stays whole."},
#            {"role": "assistant", "text": "�"}, {"role": "assistant", "text": "�"}], "Only invalid characters change")
#     equal(home.rows(f"SELECT name, input, ok, result, interrupted FROM tool_calls WHERE exchange_id = '{exchange}'"),
#           [{"name": "shell", "input": {"command": "cat binary", "nested": {"key�": ["�", "😀"]}}, "ok": True,
#             "result": {"output": "before�after 😀", "exitCode": 0}, "interrupted": True}],
#           "JSON keys, nested strings, NUL output and both flags")
#     row = home.rows(f"SELECT state, route, small_call_route FROM exchanges WHERE id = '{exchange}'")[0]
#     equal(row, {"state": "completed", "route": {**ROUTE, "model": STORED_MODEL},
#                 "small_call_route": {"driver": "codex", "model": STORED_MODEL}}, "Both stored routes are safe")
#     run_row = home.rows(f"SELECT usage, started FROM runs WHERE exchange_id = '{exchange}'")[0]
#     equal(run_row["usage"], {"model": STORED_MODEL, "inputTokens": 1, "outputTokens": 2}, "Safe usage JSON")
#     equal(run_row["started"]["model"], STORED_MODEL, "Safe started JSON")
#     check(exchange not in home.folders(hidden=True), "Invalid characters left the chat busy.")
# TEST-TIER-DISABLED-END contract/conformance/rct_conformance/scenarios/r17.py::run

# TEST-TIER-IMPORTS-BEGIN contract/conformance/rct_conformance/scenarios/r17.py:5
# import json
# TEST-TIER-IMPORTS-END contract/conformance/rct_conformance/scenarios/r17.py:5

# TEST-TIER-IMPORTS-BEGIN contract/conformance/rct_conformance/scenarios/r17.py:7
# from ..home import ROUTE, ScenarioHome
# TEST-TIER-IMPORTS-END contract/conformance/rct_conformance/scenarios/r17.py:7

# TEST-TIER-IMPORTS-BEGIN contract/conformance/rct_conformance/scenarios/r17.py:8
# from ..judge import check, equal
# TEST-TIER-IMPORTS-END contract/conformance/rct_conformance/scenarios/r17.py:8

# TEST-TIER-IMPORTS-BEGIN contract/conformance/rct_conformance/scenarios/r17.py:9
# from .r1 import END_SECONDS, accepted
# TEST-TIER-IMPORTS-END contract/conformance/rct_conformance/scenarios/r17.py:9

raise RuntimeError("Mid-tier checks require an explicitly requested testing task; see MID_TIER.md.")
