# Test implementations moved to tests/mid/archived/contract/conformance/rct_conformance/scenarios/r19.py.
"""R19: small calls (RCT-4).

Three parts: a start without a small-call route; one with a route whose small call completes; one whose small call
fails. The suite judges: without a route, no run with `"tools": "none"`; a small call that ran was a run with
`"tools": "none"` on the route handed, and left a `smallRun` line and a `runs` row of the kind `small` with its usage;
the Exchange completed in every part. A Trunk that makes no small call passes when every part completes.

Covers RCT-1.11 and 2.22.
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from ..home import ScenarioHome

SMALL_ROUTE = {"driver": "claude", "subscription": "standin", "model": "standin-small"}
PARTS: dict[str, dict[str, str] | None] = {"none": None, "completes": SMALL_ROUTE, "fails": SMALL_ROUTE}


def small_calls(records: list[Any]) -> list[Any]:
    return [record for record in records if isinstance(record.get("request"), dict)
            and record["request"].get("tools") == "none" and not record["request"].get("chatSessionId")]


def folder_gone(home: ScenarioHome, exchange: str) -> Callable[[], bool]:
    return lambda: exchange not in home.folders(hidden=True)


def run(home: ScenarioHome) -> None:
    raise RuntimeError('Tests are commented under the tier policy; see TESTS.md. Restore only in an explicitly requested testing task.')  # TEST-TIER-REFUSAL

# Archived complete imports; restore needed names in their original scope, not at this file tail.
