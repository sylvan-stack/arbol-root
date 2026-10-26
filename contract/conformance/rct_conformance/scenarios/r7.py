"""R7: a stopped work loop is ended by its watch, including the Driver's separate vendor group (RCT-1.4)."""

from __future__ import annotations

from ..home import TIME_SCALE, ScenarioHome
from ..judge import check, equal, wait_until
from .r1 import END_SECONDS, MESSAGE, accepted
from .r10 import group_alive


def run(home: ScenarioHome) -> None:
    home.part()
    start = home.start(MESSAGE, hang=True)
    accepted(start)
    exchange = start.exchange
    first = wait_until(lambda: home.events(exchange), END_SECONDS, 'the first event before the deliberate hang')
    record = home.record(exchange)
    check(record is not None and 'end' not in record, 'The deliberate hang already wrote an end.')
    heartbeat = record['signsOfLife']['heartbeat']
    children = wait_until(home.children, END_SECONDS, 'the stand-in child in its own process group')
    groups = [start.process.pid, *children]
    budget = (60 + 1 + 5) / TIME_SCALE + 1
    wait_until(lambda: not any(group_alive(group) for group in groups), budget,
               'the stuck Trunk group and its Driver child to end')
    start.process.wait(timeout=END_SECONDS)
    after = home.record(exchange)
    check(after is not None and 'end' not in after, 'The watch removed the folder or wrote an end.')
    equal(after['signsOfLife']['heartbeat'], heartbeat, 'The hung work never raised the heartbeat')
    equal(home.events(exchange), first, 'The watch wrote no event after the first whole line')
    check(all('end' not in line for line in first), 'The hung Exchange has an end line.')
    received = wait_until(home.received, END_SECONDS, 'the stopped stand-in record')
    check('SIGTERM' in received[0]['signals'], 'The watch did not give the Driver a termination signal.')
    equal(home.rows(f"SELECT state FROM exchanges WHERE id = '{exchange}'"), [{'state': 'open'}],
          'The watch left the open Exchange to settling')
    settled = home.run(['settle', exchange])
    equal((settled.status, settled.output), (0, [{'exchange': exchange, 'settled': 'interrupted'}]),
          'The hung Exchange was settled as interrupted')
    check(exchange not in home.folders(hidden=True), 'Settling left the hung folder.')
    equal(home.rows(f"SELECT state FROM exchanges WHERE id = '{exchange}'"), [{'state': 'interrupted'}],
          'The saved interrupted state')
    equal(home.rows(f"SELECT kind, outcome FROM runs WHERE exchange_id = '{exchange}'"),
          [{'kind': 'agent', 'outcome': 'interrupted'}], 'The recovered interrupted run')
