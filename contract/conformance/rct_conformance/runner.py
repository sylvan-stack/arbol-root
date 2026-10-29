# Test implementations moved to tests/mid/archived/contract/conformance/rct_conformance/runner.py.
"""Running the scenarios, each in a home of its own, with R16 after each, and reporting them (RCT-4)."""

from __future__ import annotations

from collections.abc import Callable

from .home import ScenarioHome
from .registry import Scenario

MakeHome = Callable[[Scenario], ScenarioHome]


def run_suite(selected: list[Scenario], make_home: MakeHome, write: Callable[[str], None]) -> int:
    raise RuntimeError('Tests are commented under the tier policy; see TESTS.md. Restore only in an explicitly requested testing task.')  # TEST-TIER-REFUSAL

# Archived complete imports; restore needed names in their original scope, not at this file tail.
