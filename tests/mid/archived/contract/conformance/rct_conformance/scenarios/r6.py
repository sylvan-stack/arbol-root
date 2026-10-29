"""R6: a silent Driver, a running tool and a question keep the work heartbeat alive (RCT-1.3)."""

from __future__ import annotations
from datetime import datetime

from .r1 import END_SECONDS, MESSAGE, accepted


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
    home.part()
    start = home.start(MESSAGE)
    accepted(start)
    exchange = start.exchange
    wait_until(lambda: home.events(exchange), END_SECONDS, 'the first Driver event')
    driver = observe(home, exchange, 'driver', 50 / TIME_SCALE)
    tool = observe(home, exchange, 'tool', 50 / TIME_SCALE)
    answer = observe(home, exchange, 'answer', 60 / TIME_SCALE)
    check(datetime.fromisoformat(driver['since']) < datetime.fromisoformat(tool['since']) <
          datetime.fromisoformat(answer['since']), 'since did not move with each change of wait.')
    opened = next(line['event'] for line in home.events(exchange) if line.get('event', {}).get('type') == 'ask_opened')
    home.control(exchange, {'type': 'answer', 'askId': opened['askId'],
                            'answer': {'type': 'answers', 'answers': {'branch': ['main']}}})
    wait_until(lambda: exchange not in home.folders(hidden=True), END_SECONDS, 'the healthy Exchange to complete')
    equal(home.rows(f"SELECT state FROM exchanges WHERE id = '{exchange}'"), [{'state': 'completed'}],
          'The Exchange survived its long intentional waits')

# Archived complete imports; restore needed names in their original scope, not at this file tail.
