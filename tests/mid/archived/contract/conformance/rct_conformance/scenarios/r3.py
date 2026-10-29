
# LOW TIER — DO NOT ENABLE OR RECREATE
# Historical examples only. Read before adding related tests; never execute.
# LOW-TIER-BEGIN: tests/mid/archived/contract/conformance/rct_conformance/scenarios/r3.py::run
# Reason: Mostly straightforward invalid-input/status variants; real same-chat concurrency and database-outage behavior are already retained in R5 and R12. Case reviewed: Run.
# Source: arbol-root@ef4fd6a30eca7130653b20e5eedf0da7be72aaa4:tests/mid/archived/contract/conformance/rct_conformance/scenarios/r3.py
# Historical fixtures and class context are available at the source revision; no active dependencies restored.
# LOW-TIER-SOURCE-BEGIN
# def run(home: ScenarioHome) -> None:
#     refused(home, "option", "invalid_input", options=("--bogus",))
#     refused(home, "no message", "invalid_input", message=None)
#     refused(home, "root", "invalid_input", root="../rct")
#     refused(home, "relative folder", "invalid_input", options=("--cwd", "."))
#     refused(home, "missing folder", "invalid_input", request={"workingFolder": str(home.home / "missing")})
#     refused(home, "replaces", "invalid_input", request={"replaces": str(uuid.uuid4())})
#     refused(home, "unknown root", "unknown_root", root=UNKNOWN_ROOT)
#     record_file = home.root_folder / "root.json"
#     record = json.loads(record_file.read_text(encoding="utf-8"))
#     write_json(record_file, {**record, "rootContract": home.root_contract + VERSION_NO_BUILD_LISTS})
#     try:
#         refused(home, "version", "contract_mismatch")
#     finally:
#         write_json(record_file, record)
#     busy_chat(home)
#     refused(home, "database away", "database_unavailable", database_away=True)
# LOW-TIER-SOURCE-END
# LOW-TIER-END
