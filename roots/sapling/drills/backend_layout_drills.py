"""Explicit merged-source manager Builds and additive backend layouts, preview by default."""

from __future__ import annotations

import argparse
import json
import signal
import sys
from pathlib import Path
from types import FrameType
from typing import Any

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "contract/conformance"))
from drill_support import Inspector, Places, new_json, require  # noqa: E402
from migration_support import MigrationFrame, Snapshot  # noqa: E402
from rct_conformance.tables import CATALOG  # noqa: E402
from sapling_creation import merged_source  # noqa: E402

BACKEND = ("drafts", "chat_settings", "chat_marks", "exchange_notes")
ROOTS = ("sapling", "jensen")


def state(places: Places, root: str) -> dict[str, Any]:
    inspector = Inspector(places, root=root)
    tables = inspector.read(
        "SELECT coalesce(json_agg(n.nspname||'.'||c.relname ORDER BY n.nspname,c.relname),'[]'::json) "
        "FROM pg_class c JOIN pg_namespace n ON n.oid=c.relnamespace WHERE c.relkind IN ('r','p') "
        "AND n.nspname NOT LIKE 'pg_%' AND n.nspname<>'information_schema'"
    )
    old = {"public." + name for name in ("chats", "exchanges", "messages", "tool_calls", "runs")}
    if root == "jensen":
        old.add("public.migrated_chats")
    allowed = old | {"public." + name for name in BACKEND}
    require(set(tables) in (old, allowed), "Unexpected/partial Root tables require inspection before layout.")
    schema = inspector.read("SELECT json_build_object FROM (" + CATALOG + ") AS schema_view")
    result = {"history": Snapshot(inspector, provenance=root == "jensen").read(), "schema": schema, "tables": tables}
    if set(tables) == allowed:
        counts = inspector.read(
            "SELECT json_build_object("
            + ",".join("'" + name + "',(SELECT count(*) FROM " + name + ")" for name in BACKEND)
            + ")"
        )
        revision = inspector.read(
            "SELECT json_build_object('last_value',last_value,'is_called',is_called) FROM drafts_revision"
        )
        result["backend"] = {"counts": counts, "counter": revision}
    return result


def preserved(before: dict[str, Any], after: dict[str, Any]) -> None:
    require(
        before["history"]["tables"] == after["history"]["tables"], "An older Root row changed during backend layout."
    )
    for kind, values in before["schema"].items():
        require(set(values) <= set(after["schema"].get(kind, [])), "An older schema object changed: " + kind)
    require("backend" not in before, "The backend layout is already present; inspect its earlier attempt.")
    require(
        after.get("backend")
        == {"counts": {name: 0 for name in BACKEND}, "counter": {"last_value": 1, "is_called": False}},
        "The new backend tables/counter were not empty/unconsumed.",
    )


def run() -> dict[str, Any]:
    places = Places.owner()
    receipts = places.evidence / "backend-layouts"
    require(not list(receipts.glob("*/planned.json")), "This layout phase already started; inspect before recovery.")
    frame = MigrationFrame("backend-layouts", current="jensen")
    attempt = receipts / frame.evidence.name
    new_json(attempt / "planned.json", {"roots": list(ROOTS), "realMessages": 0, "evidence": str(frame.evidence)})
    results: dict[str, Any] = {}
    try:
        try:
            source = places.home / "repos/sylvan-stack/readonly/arbol-root"
            commit = merged_source(source)
            catalogue = frame.calls.run("arbol-roots", "list")
            before = {root: state(places, root) for root in ROOTS}
            for root in ROOTS:
                require("backend" not in before[root], "The backend layout is already applied in " + root + ".")
                new_json(frame.evidence / (root + "-before.json"), before[root])
            # Qualify both packages before applying either layout.
            for root in ROOTS:
                built = frame.calls.run(
                    "arbol-builds", "build", "arbol-root", "--root", root, "--repo", str(source), seconds=1200
                )
                new_json(frame.evidence / (root + "-build.json"), built)
                require(
                    built.get("status") == "working"
                    and built.get("root") == root
                    and built.get("checks")
                    == [{"name": name, "passed": True} for name in ("unit", "layout", "migration")]
                    and built.get("source", {}).get("commit") == commit
                    and built["source"].get("branch") == "main"
                    and built["source"].get("uncommittedChanges") is False,
                    "A manager Build was not qualified from merged source.",
                )
                results[root] = {"build": built["build"]}
            for root in ROOTS:
                # Building used only private test servers; recheck that nothing appeared meanwhile.
                unchanged = state(places, root)
                require(
                    unchanged["history"]["tables"] == before[root]["history"]["tables"]
                    and unchanged["schema"] == before[root]["schema"],
                    "The Root changed during package qualification.",
                )
                applied = frame.calls.run("arbol-roots", "layout", root, seconds=90)
                new_json(frame.evidence / (root + "-layout.json"), applied)
                require(applied.get("rootBuild") == results[root]["build"], "Layout selected another manager Build.")
                after = state(places, root)
                preserved(before[root], after)
                new_json(frame.evidence / (root + "-after.json"), after)
                results[root]["layout"] = applied
            require(frame.calls.run("arbol-roots", "list") == catalogue, "Root metadata/current selection changed.")
        except BaseException as error:
            new_json(
                attempt / "failure.json",
                {"error": str(error), "next": "Inspect exact saved Build/layout state; do not replay."},
            )
            raise
    finally:
        frame.close()
    result = {
        "check": "sapling.backend-layouts",
        **frame.proof(),
        "sourceCommit": commit,
        "roots": results,
        "olderRowsAndSchemaPreserved": True,
        "catalogueUnchanged": True,
        "realMessages": 0,
    }
    new_json(attempt / "qualified.json", result)
    new_json(frame.evidence / "qualified.json", result)
    return result


def entry() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run", action="store_true")
    args = parser.parse_args()
    previous = {number: signal.getsignal(number) for number in (signal.SIGINT, signal.SIGTERM)}

    def interrupted(number: int, _frame: FrameType | None) -> None:
        raise KeyboardInterrupt("Backend layout drill interrupted by " + str(number))

    try:
        for number in previous:
            signal.signal(number, interrupted)
        print(json.dumps(run() if args.run else {"preflightOnly": True, "roots": list(ROOTS), "realMessages": 0}))
        return 0
    except (Exception, KeyboardInterrupt) as error:
        print(json.dumps({"passed": False, "error": str(error)}))
        return 1
    finally:
        for number, handler in previous.items():
            signal.signal(number, handler)
