# Mid-tier source from contract/conformance/rct_conformance/scenarios/r6.py; see MID_TIER.md.
# Shared helpers and refusal entry points remain at the original path.

# TEST-TIER-DISABLED-BEGIN contract/conformance/rct_conformance/scenarios/r6.py::run
# def run(home: ScenarioHome) -> None:
#     home.part()
#     start = home.start(MESSAGE)
#     accepted(start)
#     exchange = start.exchange
#     wait_until(lambda: home.events(exchange), END_SECONDS, 'the first Driver event')
#     driver = observe(home, exchange, 'driver', 50 / TIME_SCALE)
#     tool = observe(home, exchange, 'tool', 50 / TIME_SCALE)
#     answer = observe(home, exchange, 'answer', 60 / TIME_SCALE)
#     check(datetime.fromisoformat(driver['since']) < datetime.fromisoformat(tool['since']) <
#           datetime.fromisoformat(answer['since']), 'since did not move with each change of wait.')
#     opened = next(line['event'] for line in home.events(exchange) if line.get('event', {}).get('type') == 'ask_opened')
#     home.control(exchange, {'type': 'answer', 'askId': opened['askId'],
#                             'answer': {'type': 'answers', 'answers': {'branch': ['main']}}})
#     wait_until(lambda: exchange not in home.folders(hidden=True), END_SECONDS, 'the healthy Exchange to complete')
#     equal(home.rows(f"SELECT state FROM exchanges WHERE id = '{exchange}'"), [{'state': 'completed'}],
#           'The Exchange survived its long intentional waits')
# TEST-TIER-DISABLED-END contract/conformance/rct_conformance/scenarios/r6.py::run

# TEST-TIER-IMPORTS-BEGIN contract/conformance/rct_conformance/scenarios/r6.py:6
# from datetime import datetime
# TEST-TIER-IMPORTS-END contract/conformance/rct_conformance/scenarios/r6.py:6

# TEST-TIER-IMPORTS-BEGIN contract/conformance/rct_conformance/scenarios/r6.py:11
# from .r1 import END_SECONDS, MESSAGE, accepted
# TEST-TIER-IMPORTS-END contract/conformance/rct_conformance/scenarios/r6.py:11

raise RuntimeError("Mid-tier checks require an explicitly requested testing task; see MID_TIER.md.")
