# Test implementations moved to tests/mid/archived/contract/conformance/rct_conformance/scenarios/r6.py.
"""R6: a silent Driver, a running tool and a question keep the work heartbeat alive (RCT-1.3)."""

from __future__ import annotations

import time
from typing import Any

from ..home import TIME_SCALE, ScenarioHome
from ..judge import check, equal, wait_until
from .r1 import END_SECONDS


def observe(home: ScenarioHome, exchange: str, waiting: str, seconds: float) -> dict[str, Any]:
    def state() -> dict[str, Any] | None:
        record = home.record(exchange)
        return record['signsOfLife'] if record and record['signsOfLife']['waitingFor'] == waiting else None
    initial = wait_until(state, END_SECONDS, 'waitingFor ' + waiting)
    first, last, changed = initial['heartbeat'], initial['heartbeat'], time.monotonic()
    deadline = time.monotonic() + seconds
    while time.monotonic() < deadline:
        current = state()
        check(current is not None, 'The Trunk lost its ' + waiting + ' wait before the silent period ended.')
        assert current is not None
        equal(current['since'], initial['since'], 'since remains stable during ' + waiting)
        heartbeat = current['heartbeat']
        check(isinstance(heartbeat, int) and not isinstance(heartbeat, bool) and heartbeat >= last,
              'The heartbeat moved backwards or stopped being a counter.', last, heartbeat)
        if heartbeat > last:
            last, changed = heartbeat, time.monotonic()
        check(time.monotonic() - changed <= 10 / TIME_SCALE + 0.25,
              'The heartbeat stood still for more than ten divided seconds while waiting for ' + waiting + '.')
        time.sleep(0.05)
    check(last > first, 'The work never raised the heartbeat during ' + waiting + '.')
    return initial


def run(home: ScenarioHome) -> None:
    raise RuntimeError('Tests are commented under the tier policy; see TESTS.md. Restore only in an explicitly requested testing task.')  # TEST-TIER-REFUSAL

# Archived complete imports; restore needed names in their original scope, not at this file tail.
