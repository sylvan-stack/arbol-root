from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))
from management_support import Fixture  # noqa: E402


class MovingClock:
    def __init__(self) -> None:
        self.value = 0.0
        self.pauses: list[float] = []

    def now(self) -> float:
        return self.value

    def pause(self, seconds: float) -> None:
        self.pauses.append(seconds)
        self.value += seconds


class Stopping(unittest.TestCase):
    def setUp(self) -> None:
        self.f = Fixture(self)

# TEST-TIER-DISABLED-BEGIN tests/test_stop.py::Stopping.test_missing_exchange_is_none_without_launching_or_creating_control
#     def test_missing_exchange_is_none_without_launching_or_creating_control(self) -> None:
#         """root.stop-none"""
#         name = record(1)['exchange']
#         reply = self.f.cli('stop', name)
#         self.assertEqual(reply.returncode, 0, reply.stderr)
#         self.assertEqual(json.loads(reply.stdout), {'root':'sapling','exchange':name,'ended':'none','forced':False})
#         self.assertEqual(list(self.f.exchanges.iterdir()), [])
#         self.assertEqual(self.f.calls(), [])
# TEST-TIER-DISABLED-END tests/test_stop.py::Stopping.test_missing_exchange_is_none_without_launching_or_creating_control

# TEST-TIER-DISABLED-BEGIN tests/test_stop.py::Stopping.test_dead_process_is_settled_without_a_stop_line_and_reports_the_observed_state
#     def test_dead_process_is_settled_without_a_stop_line_and_reports_the_observed_state(self) -> None:
#         """root.stop-dead"""
#         value = record(1, ended=True)
#         folder = self.f.put(value)
#         for settled, expected in [('completed','completed'),('failed','failed'),('cancelled','cancelled'),
#                                   ('interrupted','interrupted'),('none','saved')]:
#             with self.subTest(settled=settled), mock.patch('arbol_root.process.started_at', return_value=None):
#                 with mock.patch('arbol_root.stop.settle_after_stop', return_value={'exchange':value['exchange'],
#                                                                                 'settled':settled}):
#                     reply = stop(self.f.context, value['exchange'])
#             self.assertEqual((reply.value['ended'],reply.value['forced']), (expected,False))
#         self.assertEqual((folder / 'control').read_bytes(), b'')
# TEST-TIER-DISABLED-END tests/test_stop.py::Stopping.test_dead_process_is_settled_without_a_stop_line_and_reports_the_observed_state

# TEST-TIER-DISABLED-BEGIN tests/test_stop.py::Stopping.test_settling_refusal_keeps_a_dead_stop_successful_with_its_known_end
#     def test_settling_refusal_keeps_a_dead_stop_successful_with_its_known_end(self) -> None:
#         """root.stop-settle-refusal"""
#         value = record(1, ended=True)
#         self.f.put(value)
#         refusal = {'exchange':value['exchange'], 'error':{'code':'database_unavailable','message':'offline'}}
#         with mock.patch('arbol_root.process.started_at', return_value=None):
#             with mock.patch('arbol_root.stop.settle_after_stop', return_value=refusal):
#                 reply = stop(self.f.context, value['exchange'])
#         self.assertEqual(reply.status, 0)
#         self.assertEqual(reply.value['ended'], 'completed')
#         self.assertEqual(reply.value['settling'], refusal)
#         del value['end']
#         self.f.put(value)
#         with mock.patch('arbol_root.process.started_at', return_value=None):
#             with mock.patch('arbol_root.stop.settle_after_stop', return_value=refusal):
#                 self.assertEqual(stop(self.f.context, value['exchange']).value['ended'], 'interrupted')
# TEST-TIER-DISABLED-END tests/test_stop.py::Stopping.test_settling_refusal_keeps_a_dead_stop_successful_with_its_known_end

# TEST-TIER-DISABLED-BEGIN tests/test_stop.py::Stopping.test_cooperative_stop_appends_once_and_preserves_an_existing_answer_line
#     def test_cooperative_stop_appends_once_and_preserves_an_existing_answer_line(self) -> None:
#         """root.stop-control"""
#         value = record(1)
#         folder, _child = self.f.live(value, 'cooperate')
#         answer = b'{"type":"answer","askId":"private","answer":{}}\n'
#         (folder / 'control').write_bytes(answer)
#         reply = self.f.cli('stop', value['exchange'])
#         self.assertEqual(reply.returncode, 0, reply.stderr)
#         result = json.loads(reply.stdout)
#         self.assertIn(result['ended'], ['cancelled','interrupted'])
#         # The process may exit just after writing end, in which case settling wins the observation.
#         self.assertFalse(result['forced'])
#         self.assertEqual((folder / 'control').read_bytes(), answer+b'{"type":"stop"}\n')
# TEST-TIER-DISABLED-END tests/test_stop.py::Stopping.test_cooperative_stop_appends_once_and_preserves_an_existing_answer_line

# TEST-TIER-DISABLED-BEGIN tests/test_stop.py::Stopping.test_disappearing_folder_after_a_stop_is_saved
#     def test_disappearing_folder_after_a_stop_is_saved(self) -> None:
#         """root.stop-disappearance"""
#         value = record(1)
#         self.f.live(value, 'remove')
#         reply = self.f.cli('stop', value['exchange'])
#         self.assertEqual(reply.returncode, 0, reply.stderr)
#         self.assertEqual(json.loads(reply.stdout)['ended'], 'saved')
# TEST-TIER-DISABLED-END tests/test_stop.py::Stopping.test_disappearing_folder_after_a_stop_is_saved

# TEST-TIER-DISABLED-BEGIN tests/test_stop.py::Stopping.test_already_ended_living_record_is_not_written_or_signalled
#     def test_already_ended_living_record_is_not_written_or_signalled(self) -> None:
#         """root.stop-ended"""
#         value = record(1)
#         folder, child = self.f.live(value)
#         value['end'] = {'state':'failed', 'at':'2026-10-26T12:00:00.000Z'}
#         (folder / 'record.json').write_text(json.dumps(value))
#         reply = stop(self.f.context, value['exchange'])
#         self.assertEqual(reply.value['ended'], 'failed')
#         self.assertEqual((folder / 'control').read_bytes(), b'')
#         self.assertIsNone(child.poll())
#         self.assertEqual(self.f.calls(), [])
# TEST-TIER-DISABLED-END tests/test_stop.py::Stopping.test_already_ended_living_record_is_not_written_or_signalled

# TEST-TIER-DISABLED-BEGIN tests/test_stop.py::Stopping.test_publication_wait_is_bounded_and_picks_up_a_newly_published_record
#     def test_publication_wait_is_bounded_and_picks_up_a_newly_published_record(self) -> None:
#         """root.stop-publication"""
#         value = record(1)
#         pending = self.f.exchanges / ('.'+value['exchange']+'.new')
#         pending.mkdir()
#         clock = MovingClock()
#         reply = stop(self.f.context, value['exchange'], clock=clock.now, pause=clock.pause)
#         self.assertEqual(reply.value['ended'], 'none')
#         self.assertAlmostEqual(clock.value, 15)
#         self.assertTrue(all(0 <= seconds <= 0.1 for seconds in clock.pauses))
#         clock = MovingClock()
#         def publish(seconds: float) -> None:
#             clock.pause(seconds)
#             self.f.put(value)
#             pending.rmdir()
#         with mock.patch('arbol_root.process.started_at', return_value=None):
#             with mock.patch('arbol_root.stop.settle_after_stop', return_value={'settled':'interrupted'}):
#                 reply = stop(self.f.context, value['exchange'], clock=clock.now, pause=publish)
#         self.assertEqual(reply.value['ended'], 'interrupted')
#         self.assertEqual(clock.value, 0.1)
# TEST-TIER-DISABLED-END tests/test_stop.py::Stopping.test_publication_wait_is_bounded_and_picks_up_a_newly_published_record

# TEST-TIER-DISABLED-BEGIN tests/test_stop.py::Stopping.test_nonregular_missing_or_symlink_control_refuses_without_force
#     def test_nonregular_missing_or_symlink_control_refuses_without_force(self) -> None:
#         """root.stop-control-refusal"""
#         value = record(1)
#         folder, child = self.f.live(value)
#         path = folder / 'control'
#         path.unlink()
#         for kind in ['missing', 'fifo', 'symlink']:
#             with self.subTest(kind=kind):
#                 if kind == 'fifo':
#                     os.mkfifo(path)
#                 elif kind == 'symlink':
#                     path.symlink_to(self.f.base / 'outside-control')
#                 with self.assertRaises(Refusal) as error:
#                     stop(self.f.context, value['exchange'])
#                 self.assertEqual(error.exception.code, 'root_unavailable')
#                 self.assertIsNone(child.poll())
#                 path.unlink(missing_ok=True)
# TEST-TIER-DISABLED-END tests/test_stop.py::Stopping.test_nonregular_missing_or_symlink_control_refuses_without_force

# TEST-TIER-DISABLED-BEGIN tests/test_stop.py::Stopping.test_short_control_write_is_not_retried
#     def test_short_control_write_is_not_retried(self) -> None:
#         """root.stop-short-write"""
#         value = record(1)
#         self.f.live(value)
#         with mock.patch('arbol_root.stop.os.write', return_value=1) as write:
#             with self.assertRaises(Refusal) as error:
#                 stop(self.f.context, value['exchange'])
#         self.assertEqual(error.exception.code, 'root_unavailable')
#         write.assert_called_once()
# TEST-TIER-DISABLED-END tests/test_stop.py::Stopping.test_short_control_write_is_not_retried

# TEST-TIER-DISABLED-BEGIN tests/test_stop.py::Stopping.test_reused_pid_is_treated_as_gone_and_never_signalled
#     def test_reused_pid_is_treated_as_gone_and_never_signalled(self) -> None:
#         """root.stop-process-identity"""
#         value = record(1)
#         folder, child = self.f.live(value)
#         value['process']['startedAt'] = '2000-01-01T00:00:00.000Z'
#         (folder / 'record.json').write_text(json.dumps(value))
#         with mock.patch('arbol_root.stop.force_end') as force:
#             with mock.patch('arbol_root.stop.settle_after_stop', return_value={'settled':'interrupted'}):
#                 reply = stop(self.f.context, value['exchange'], True)
#         self.assertFalse(reply.value['forced'])
#         force.assert_not_called()
#         self.assertIsNone(child.poll())
#         self.assertEqual((folder / 'control').read_bytes(), b'')
# TEST-TIER-DISABLED-END tests/test_stop.py::Stopping.test_reused_pid_is_treated_as_gone_and_never_signalled

# TEST-TIER-DISABLED-BEGIN tests/test_stop.py::Stopping.test_graceful_deadline_calls_escalation_after_twenty_awake_seconds
#     def test_graceful_deadline_calls_escalation_after_twenty_awake_seconds(self) -> None:
#         """root.stop-grace-clock"""
#         value = record(1)
#         self.f.live(value)
#         clock = MovingClock()
#         def ended(*_args: Any) -> bool:
#             self.assertAlmostEqual(clock.value, 20)
#             return True
#         with mock.patch('arbol_root.stop.force_end', side_effect=ended):
#             with mock.patch('arbol_root.stop.settle_after_stop', return_value={'settled':'interrupted'}):
#                 # Keep the actual short-lived fixture live, but avoid hundreds of ps launches in a moved-clock check.
#                 with mock.patch('arbol_root.stop.read_exchange') as read:
#                     from arbol_root.stop import Observed
#                     read.return_value = Observed(value['process'], True, None)
#                     reply = stop(self.f.context, value['exchange'], clock=clock.now, pause=clock.pause)
#         self.assertTrue(reply.value['forced'])
#         self.assertTrue(all(seconds <= 0.1 for seconds in clock.pauses))
# TEST-TIER-DISABLED-END tests/test_stop.py::Stopping.test_graceful_deadline_calls_escalation_after_twenty_awake_seconds

# Archived complete imports; restore needed names in their original scope, not at this file tail.
# TEST-TIER-IMPORTS-BEGIN tests/test_stop.py:3
# import json
# TEST-TIER-IMPORTS-END tests/test_stop.py:3
# TEST-TIER-IMPORTS-BEGIN tests/test_stop.py:4
# import os
# TEST-TIER-IMPORTS-END tests/test_stop.py:4
# TEST-TIER-IMPORTS-BEGIN tests/test_stop.py:8
# from typing import Any
# TEST-TIER-IMPORTS-END tests/test_stop.py:8
# TEST-TIER-IMPORTS-BEGIN tests/test_stop.py:9
# from unittest import mock
# TEST-TIER-IMPORTS-END tests/test_stop.py:9
# TEST-TIER-IMPORTS-BEGIN tests/test_stop.py:13
# from test_listing import record  # noqa: E402
# TEST-TIER-IMPORTS-END tests/test_stop.py:13
# TEST-TIER-IMPORTS-BEGIN tests/test_stop.py:15
# from arbol_root.model import Refusal  # noqa: E402
# TEST-TIER-IMPORTS-END tests/test_stop.py:15
# TEST-TIER-IMPORTS-BEGIN tests/test_stop.py:16
# from arbol_root.stop import stop  # noqa: E402
# TEST-TIER-IMPORTS-END tests/test_stop.py:16
