"""Subscriptions Vigor's tables (SGM-1): fictional rows for Root-owned SQL qualification, and the guarded installed step.

Without `--run` the script previews and touches nothing. With `--run` it builds a manager of each retained Root from
merged readonly source, qualifies it, and applies the additive layouts to both retained Roots with `arbol-roots layout`,
proving every older row, schema object and backend row unchanged and the three Vigor tables present and empty.
"""

from __future__ import annotations

import argparse
import json
import signal
import sys
from decimal import Decimal
from pathlib import Path
from types import FrameType
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from rct_conformance.postgres import Server

ROOT = Path(__file__).resolve().parents[1]
TABLES = ("vigor_profiles", "vigor_reports", "vigor_results")
INDEX = "vigor_results_subscription"
BACKEND = ("drafts", "chat_settings", "chat_marks", "exchange_notes")
ROOTS = ("sapling", "jensen")
REPORTS = [f"40000000-0000-4000-8000-{n:012d}" for n in range(1, 3)]
RESULTS = [f"41000000-0000-4000-8000-{n:012d}" for n in range(1, 3)]


def rows(server: Server, database: str) -> dict[str, list[dict[str, Any]]]:
    """Keep numeric JSON exact instead of comparing rounded Python floats."""
    return {
        table: [
            json.loads(row["value"], parse_float=Decimal)
            for row in server.rows(
                database, f"SELECT row_to_json(t)::text AS value FROM {table} t ORDER BY row_to_json(t)::text"
            )
        ]
        for table in TABLES
    }


def present(server: Server, database: str) -> bool:
    names = (*TABLES, INDEX)
    value = server.value(
        database,
        "SELECT json_build_array(" + ",".join("to_regclass('public." + name + "') IS NOT NULL" for name in names) + ")",
    )
    if any(value) and not all(value):
        raise ValueError("The Vigor qualification fixture has a partial layout.")
    return bool(all(value))


def seed(server: Server, database: str) -> None:
    """Fictional rows of the three tables: profile 1, a Claude report with its result, an unsupported z.ai report."""
    if not present(server, database):
        return
    windows = (
        '[{"kind":"session","label":"Five hours","resource":"tokens","usedPercent":35,'
        '"resetsAt":"2026-10-26T13:20:00Z","windowMinutes":300,"limitReached":false},'
        '{"kind":"weekly","label":"Seven days","resource":"tokens","usedPercent":20.123456789012345678901234567890,'
        '"resetsAt":"2026-10-29T10:00:00Z","windowMinutes":10080,"limitReached":false}]'
    )
    losses = (
        '[{"label":"Five hours","resource":"tokens","countedAs":"tokens","assumed":false,"role":"gate","reached":false,'
        '"loss":0,"weight":0.1,"contribution":0,"reason":null,"predicted":false,"usedPercent":35,'
        '"resetsAt":"2026-10-26T13:20:00Z","windowMinutes":300},'
        '{"label":"Seven days","resource":"tokens","countedAs":"tokens","assumed":false,"role":"store","reached":false,'
        '"loss":0.37023809523809526,"weight":1,"contribution":0.37023809523809526,"reason":null,"predicted":false,'
        '"usedPercent":20.123456789012345678901234567890,"resetsAt":"2026-10-29T10:00:00Z","windowMinutes":10080}]'
    )
    server.execute(
        database,
        f"""
INSERT INTO vigor_profiles VALUES
 (1,'proposed','even',0.1,'[]','shortest-window','2026-10-27T12:00:00Z');
INSERT INTO vigor_reports VALUES
 ('{REPORTS[0]}','claude','anthropic','anthropic','ok','2026-10-26T09:55:00Z',NULL,'{windows}','{{"isUsingOverage":false}}','2026-10-26T10:00:00Z',NULL),
 ('{REPORTS[1]}','pi','zai','zai','unsupported','2026-10-26T09:56:00Z','no allowance reading for zai through Pi 🌲','[]','{{}}','2026-10-26T10:00:01Z','50000000-0000-4000-8000-000000000001');
INSERT INTO vigor_results VALUES
 ('{RESULTS[0]}','claude','anthropic','anthropic','2026-10-26T10:00:00Z','{REPORTS[0]}',1,'{losses}',0.37023809523809526,false,false,NULL,NULL,'[]','2026-10-26T13:20:00Z',0.3912698412698413),
 ('{RESULTS[1]}','pi','zai','zai','2026-10-26T10:00:00Z','{REPORTS[1]}',1,'[]',NULL,false,false,'5 hours 5 minutes','allowance not supported for zai','["why 🌲"]',NULL,NULL);
""",
    )


def state(places: Any, root: str) -> dict[str, Any]:
    """Read one retained Root: its history rows, its schema, its backend rows and counter, and the Vigor tables' counts."""
    from drill_support import Inspector, require
    from migration_support import Snapshot
    from rct_conformance.tables import CATALOG

    inspector = Inspector(places, root=root)
    tables = inspector.read(
        "SELECT coalesce(json_agg(n.nspname||'.'||c.relname ORDER BY n.nspname,c.relname),'[]'::json) "
        "FROM pg_class c JOIN pg_namespace n ON n.oid=c.relnamespace WHERE c.relkind IN ('r','p') "
        "AND n.nspname NOT LIKE 'pg_%' AND n.nspname<>'information_schema'"
    )
    old = {"public." + name for name in ("chats", "exchanges", "messages", "tool_calls", "runs", *BACKEND)}
    if root == "jensen":
        old.add("public.migrated_chats")
    vigor = {"public." + name for name in TABLES}
    require(set(tables) in (old, old | vigor), "Unexpected/partial Root tables require inspection before layout.")
    schema = inspector.read("SELECT json_build_object FROM (" + CATALOG + ") AS schema_view")
    counts = inspector.read(
        "SELECT json_build_object("
        + ",".join("'" + name + "',(SELECT count(*) FROM " + name + ")" for name in BACKEND)
        + ")"
    )
    revision = inspector.read(
        "SELECT json_build_object('last_value',last_value,'is_called',is_called) FROM drafts_revision"
    )
    backend = inspector.read(
        "SELECT json_build_object("
        + ",".join(
            "'" + name + "',(SELECT coalesce(json_agg(row_to_json(t)::text ORDER BY row_to_json(t)::text),'[]') "
            "FROM " + name + " t)"
            for name in BACKEND
        )
        + ")"
    )
    result = {
        "history": Snapshot(inspector, provenance=root == "jensen").read(),
        "schema": schema,
        "tables": tables,
        "backend": {"counts": counts, "counter": revision, "rows": backend},
    }
    if set(tables) == old | vigor:
        result["vigor"] = inspector.read(
            "SELECT json_build_object("
            + ",".join("'" + name + "',(SELECT count(*) FROM " + name + ")" for name in TABLES)
            + ")"
        )
    return result


def preserved(before: dict[str, Any], after: dict[str, Any]) -> None:
    """Every older row and schema object unchanged, the backend's rows and counter too; the Vigor tables new and empty."""
    from drill_support import require

    require(before["history"]["tables"] == after["history"]["tables"], "An older Root row changed during Vigor layout.")
    for kind, values in before["schema"].items():
        require(set(values) <= set(after["schema"].get(kind, [])), "An older schema object changed: " + kind)
    require(before["backend"] == after["backend"], "A backend row or the Draft counter changed during Vigor layout.")
    require("vigor" not in before, "The Vigor layout is already present; inspect its earlier attempt.")
    require(after.get("vigor") == dict.fromkeys(TABLES, 0), "The new Vigor tables were not empty.")


def run() -> dict[str, Any]:
    sys.path.insert(0, str(ROOT / "roots/sapling/drills"))
    sys.path.insert(0, str(ROOT / "contract/conformance"))
    from drill_support import Places, new_json, require
    from migration_support import MigrationFrame
    from sapling_creation import merged_source

    places = Places.owner()
    receipts = places.evidence / "vigor-layouts"
    require(not list(receipts.glob("*/planned.json")), "This layout phase already started; inspect before recovery.")
    frame = MigrationFrame("vigor-layouts", current="jensen")
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
                require("vigor" not in before[root], "The Vigor layout is already applied in " + root + ".")
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
                    and unchanged["schema"] == before[root]["schema"]
                    and unchanged["backend"] == before[root]["backend"],
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
        "check": "sapling.vigor-layouts",
        **frame.proof(),
        "sourceCommit": commit,
        "roots": results,
        "olderRowsSchemaAndBackendPreserved": True,
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
        raise KeyboardInterrupt("Vigor layout step interrupted by " + str(number))

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


if __name__ == "__main__":
    raise SystemExit(entry())
