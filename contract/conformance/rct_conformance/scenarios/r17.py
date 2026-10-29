# Test implementations moved to tests/mid/archived/contract/conformance/rct_conformance/scenarios/r17.py.
"""R17: original event bytes, NUL and split emoji replacements in SQL, and independent tool flags."""

from __future__ import annotations

from ..home import ScenarioHome

MESSAGE = "Original\0message \ud83d and 😀."
STORED_MESSAGE = "Original�message � and 😀."
MODEL = "standin😀\0\ud83d"
STORED_MODEL = "standin😀��"


def run(home: ScenarioHome) -> None:
    raise RuntimeError('Tests are commented under the tier policy; see TESTS.md. Restore only in an explicitly requested testing task.')  # TEST-TIER-REFUSAL

# Archived complete imports; restore needed names in their original scope, not at this file tail.
