
# LOW TIER — DO NOT ENABLE OR RECREATE
# Historical examples only. Read before adding related tests; never execute.
# LOW-TIER-BEGIN: tests/mid/archived/contract/conformance/rct_conformance/scenarios/r19.py::run
# Reason: The small-call scenario permits zero small calls even when a route is supplied, so its assertions can pass without observing the advertised behavior; ordinary route fields alone do not justify retention. Case reviewed: Run.
# Source: arbol-root@ef4fd6a30eca7130653b20e5eedf0da7be72aaa4:tests/mid/archived/contract/conformance/rct_conformance/scenarios/r19.py
# Historical fixtures and class context are available at the source revision; no active dependencies restored.
# LOW-TIER-SOURCE-BEGIN
# def run(home: ScenarioHome) -> None:
#     for part, route in PARTS.items():
#         home.part(part)
#         started = home.start("Name this chat.", request={"smallCallRoute": route} if route else None)
#         exchange = accepted(started)["exchange"]
#         follow = home.follow(exchange)
#         try:
#             record = home.record(exchange)
#             check(isinstance(record, dict), f"{part}: the Exchange has no record once it is accepted.")
#             equal(record.get("smallCallRoute"), route, f"{part}: the record's smallCallRoute")
#             wait_until(folder_gone(home, exchange), END_SECONDS, f"{part}: the Exchange's folder to go")
#             lines = follow.lines()
#         finally:
#             follow.close()
#         equal(home.rows(f"SELECT state, small_call_route FROM exchanges WHERE id = '{exchange}'"),
#               [{"state": "completed", "small_call_route": route}], f"{part}: the Exchange")
#         smalls = small_calls([record for record in home.received() if record.get("part") == part])
#         small_lines = [line["smallRun"] for line in lines if isinstance(line, dict) and "smallRun" in line]
#         small_rows = home.rows(f"SELECT run_id, outcome, usage FROM runs WHERE exchange_id = '{exchange}'"
#                                " AND kind = 'small' ORDER BY run_id")
#         if route is None:
#             equal(len(smalls), 0, f"{part}: runs with tools none without a small-call route")
#         else:
#             for small in smalls:
#                 check(small["launcher"] == f"arbol-{route['driver']}-driver"
#                       and small["request"].get("subscriptionId") == route["subscription"]
#                       and small["request"].get("model") == route["model"],
#                       f"{part}: a small call ran on another route than the one handed.", route, small["request"])
#         equal(len(small_lines), len(smalls), f"{part}: the smallRun lines of the small calls that ran")
#         equal(len(small_rows), len(smalls), f"{part}: the runs of the kind small")
#         for row in small_rows:
#             check(isinstance(row["usage"], dict) and row["usage"], f"{part}: a small call's run has no usage.",
#                   "its usage", row)
# LOW-TIER-SOURCE-END
# LOW-TIER-END
