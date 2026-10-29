# Mid-tier source from contract/conformance/rct_conformance/scenarios/r3.py; see MID_TIER.md.
# Shared helpers and refusal entry points remain at the original path.

# TEST-TIER-DISABLED-BEGIN contract/conformance/rct_conformance/scenarios/r3.py::run
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
# TEST-TIER-DISABLED-END contract/conformance/rct_conformance/scenarios/r3.py::run

# TEST-TIER-IMPORTS-BEGIN contract/conformance/rct_conformance/scenarios/r3.py:13
# import json
# TEST-TIER-IMPORTS-END contract/conformance/rct_conformance/scenarios/r3.py:13

# TEST-TIER-IMPORTS-BEGIN contract/conformance/rct_conformance/scenarios/r3.py:22
# from ..home import ROOT, ROUTE, ScenarioHome, write_json
# TEST-TIER-IMPORTS-END contract/conformance/rct_conformance/scenarios/r3.py:22

raise RuntimeError("Mid-tier checks require an explicitly requested testing task; see MID_TIER.md.")
