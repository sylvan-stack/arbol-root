# Mid-tier source from contract/conformance/rct_conformance/scenarios/r8.py; see MID_TIER.md.
# Shared helpers and refusal entry points remain at the original path.

# TEST-TIER-DISABLED-BEGIN contract/conformance/rct_conformance/scenarios/r8.py::run
# def run(home: ScenarioHome) -> None:
#     stopped(home, "text", lambda events: len([e for e in events if e.get("type") == "text_delta"]) >= 2)
#     calls = stopped(home, "tool", lambda events: any(e.get("type") == "tool_started" for e in events))
#     equal([{key: call[key] for key in ("name", "ok", "interrupted")} for call in calls],
#           [{"name": "shell", **INTERRUPTED}], "tool: the shell call that was running")
#     asks: list[Any] = []
#
#     def asked(events: list[dict[str, Any]]) -> bool:
#         asks[:] = [event["ask"] for event in events if event.get("type") == "ask_opened"]
#         return bool(asks)
#
#     calls = stopped(home, "ask", asked)
#     equal(calls, [{"name": "ask_user", **INTERRUPTED, "ask": asks[0], "answer": None}],
#           "ask: the question that was open")
#     early(home)
# TEST-TIER-DISABLED-END contract/conformance/rct_conformance/scenarios/r8.py::run


raise RuntimeError("Mid-tier checks require an explicitly requested testing task; see MID_TIER.md.")
