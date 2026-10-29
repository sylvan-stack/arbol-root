# Test implementations moved to tests/mid/archived/contract/conformance/rct_conformance/scenarios/r10.py.
"""R10: SIGTERM leaves no end; settling recovers the text, open call and interrupted run (RCT-2.8, 2.12)."""

from __future__ import annotations

import subprocess

from ..home import ScenarioHome


def group_alive(group: int) -> bool:
    output = subprocess.run(["/bin/ps", "-A", "-o", "pgid=,stat="], capture_output=True, text=True,
                            check=False).stdout
    return any(parts[0] == str(group) and not parts[1].startswith("Z")
               for line in output.splitlines() if len(parts := line.split()) == 2)


def run(home: ScenarioHome) -> None:
    raise RuntimeError('Tests are commented under the tier policy; see TESTS.md. Restore only in an explicitly requested testing task.')  # TEST-TIER-REFUSAL

# Archived complete imports; restore needed names in their original scope, not at this file tail.
