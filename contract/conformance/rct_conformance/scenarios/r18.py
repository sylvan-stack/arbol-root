# Test implementations moved to tests/mid/archived/contract/conformance/rct_conformance/scenarios/r18.py.
"""R18: after sixteen idle minutes on the divided awake clock, stop even with a background command."""

from __future__ import annotations

from ..home import ScenarioHome

IDLE_SECONDS = 16 * 60


def run(home: ScenarioHome) -> None:
    raise RuntimeError('Tests are commented under the tier policy; see TESTS.md. Restore only in an explicitly requested testing task.')  # TEST-TIER-REFUSAL

# Archived complete imports; restore needed names in their original scope, not at this file tail.
