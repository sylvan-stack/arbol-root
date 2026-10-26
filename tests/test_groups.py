from __future__ import annotations

import contextlib
import signal
import subprocess
import sys
import unittest
from datetime import UTC, datetime, timedelta
from pathlib import Path
from types import SimpleNamespace
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))
from management_support import Fixture  # noqa: E402
from test_listing import record  # noqa: E402
from test_stop import MovingClock  # noqa: E402

from arbol_root.clock import awake  # noqa: E402
from arbol_root.groups import continuing, force_group, members  # noqa: E402
from arbol_root.model import Identity, Refusal  # noqa: E402
from arbol_root.stop import Observed, force_end, stop  # noqa: E402

AT = datetime(2026,10,26,9,tzinfo=UTC)
PROCESS = {'pid':50,'startedAt':AT.isoformat()}


class GroupIdentity(unittest.TestCase):
    def simulated(self) -> contextlib.ExitStack:
        stack = contextlib.ExitStack()
        stack.enter_context(mock.patch('arbol_root.groups.process_alive', return_value=True))
        stack.enter_context(mock.patch('arbol_root.groups.os.getpgid', return_value=50))
        stack.enter_context(mock.patch('arbol_root.groups.os.getpgrp', return_value=99999))
        return stack

    def test_group_reader_has_clean_environment_absolute_times_and_excludes_zombies(self) -> None:
        """root.stop-group-members"""
        output = ('50 50 Ss Mon Oct 26 09:00:00 2026\n51 50 S Mon Oct 26 09:00:01 2026\n'
                  '52 50 Z Mon Oct 26 09:00:01 2026\n60 60 S Mon Oct 26 09:00:00 2026\n')
        with mock.patch('arbol_root.groups.subprocess.run', return_value=SimpleNamespace(returncode=0,stdout=output)) as run:
            found = members(50)
        self.assertEqual(found, {50:AT,51:AT+timedelta(seconds=1)})
        self.assertEqual(run.call_args.args[0], ['/bin/ps','-axo','pid=,pgid=,stat=,lstart='])
        self.assertEqual(run.call_args.kwargs['env'], {'PATH':'/usr/bin:/bin','LANG':'C','LC_ALL':'C','TZ':'UTC'})
        self.assertEqual(run.call_args.kwargs['timeout'], 5)
        self.assertEqual(run.call_args.kwargs['stdin'], subprocess.DEVNULL)
        for text in ['not a process row', '50 50 S no-time']:
            with mock.patch('arbol_root.groups.subprocess.run', return_value=SimpleNamespace(returncode=0,stdout=text)):
                with self.assertRaises(ValueError):
                    members(50)

    def test_full_escalation_uses_awake_five_second_deadlines_and_refuses_survivors(self) -> None:
        """root.stop-escalation-clock"""
        clock = MovingClock()
        calls: list[tuple[int, float]] = []
        with self.simulated():
            with mock.patch('arbol_root.groups.members', return_value={50:AT}):
                with mock.patch('arbol_root.groups.os.killpg', side_effect=lambda _group,sig:calls.append((sig,clock.value))):
                    with mock.patch('arbol_root.clock.time.time', side_effect=AssertionError('wall time is irrelevant')):
                        with self.assertRaises(Refusal) as error:
                            force_group(PROCESS, clock.now, clock.pause)
        self.assertEqual(error.exception.code, 'not_ended')
        self.assertEqual([sig for sig,_at in calls], [signal.SIGTERM,signal.SIGKILL])
        self.assertAlmostEqual(calls[0][1], 0)
        self.assertAlmostEqual(calls[1][1], 5)
        self.assertAlmostEqual(clock.value, 10)
        self.assertTrue(all(seconds <= 0.1 for seconds in clock.pauses))

    def test_os_clock_is_uptime_raw_on_this_mac(self) -> None:
        """root.stop-awake-clock"""
        import time
        with mock.patch('arbol_root.clock.time.clock_gettime', return_value=123.5) as read:
            self.assertEqual(awake(), 123.5)
        read.assert_called_once_with(getattr(time,'CLOCK_UPTIME_RAW',time.CLOCK_MONOTONIC))

    def test_complete_stop_uses_20_5_5_with_an_in_process_moved_clock(self) -> None:
        """root.stop-complete-clock"""
        clock = MovingClock()
        calls: list[tuple[int, float]] = []
        context = Identity('sapling','0','1.0.0',Path('/private-fixture'),Path('/private-launcher'))
        with self.simulated(), contextlib.ExitStack() as stack:
            stack.enter_context(mock.patch('arbol_root.groups.members', return_value={50:AT}))
            stack.enter_context(mock.patch('arbol_root.groups.os.killpg',
                                           side_effect=lambda _group,sig:calls.append((sig,clock.value))))
            stack.enter_context(mock.patch('arbol_root.stop.read_exchange', return_value=Observed(PROCESS,True,None)))
            append = stack.enter_context(mock.patch('arbol_root.stop.append_stop'))
            stack.enter_context(mock.patch('arbol_root.clock.time.time', side_effect=AssertionError('wall clock')))
            with self.assertRaises(Refusal) as error:
                stop(context,record(1)['exchange'],clock=clock.now,pause=clock.pause)
        self.assertEqual(error.exception.code, 'not_ended')
        self.assertEqual([sig for sig,_at in calls], [signal.SIGTERM,signal.SIGKILL])
        self.assertAlmostEqual(calls[0][1],20)
        self.assertAlmostEqual(calls[1][1],25)
        self.assertAlmostEqual(clock.value,30)
        append.assert_called_once()

    def test_reused_or_unanchored_group_is_never_killed_after_term(self) -> None:
        """root.stop-group-identity"""
        clock = MovingClock()
        for replacement in [{50:AT+timedelta(seconds=9)}, {51:AT}]:
            with self.subTest(replacement=replacement), self.simulated():
                with mock.patch('arbol_root.groups.members', side_effect=[{50:AT},replacement]):
                    with mock.patch('arbol_root.groups.os.killpg') as send:
                        with self.assertRaises(Refusal) as error:
                            force_group(PROCESS, clock.now, clock.pause)
            self.assertEqual(error.exception.code, 'not_ended')
            send.assert_called_once_with(50, signal.SIGTERM)

    def test_new_members_are_owned_only_while_a_verified_member_continues(self) -> None:
        child_at = AT+timedelta(seconds=1)
        with mock.patch('arbol_root.groups.members', return_value={50:AT,51:child_at}):
            known = continuing(50, {50:AT})
        with mock.patch('arbol_root.groups.members', return_value={51:child_at}):
            self.assertEqual(continuing(50, known), {51:child_at})

    def test_wrong_group_or_process_failure_refuses_before_a_signal(self) -> None:
        """root.stop-group-refusal"""
        clock = MovingClock()
        for group in [51,99999]:
            with self.simulated():
                with mock.patch('arbol_root.groups.os.getpgid', return_value=group):
                    with mock.patch('arbol_root.groups.os.killpg') as send:
                        with self.assertRaises(Refusal) as error:
                            force_group(PROCESS, clock.now, clock.pause)
                self.assertEqual(error.exception.code, 'root_unavailable')
                send.assert_not_called()
        with self.simulated(), mock.patch('arbol_root.groups.os.getpgrp', return_value=50):
            with mock.patch('arbol_root.groups.os.killpg') as send:
                with self.assertRaises(Refusal):
                    force_group(PROCESS, clock.now, clock.pause)
            send.assert_not_called()
        with mock.patch('arbol_root.groups.process_alive', return_value=False):
            with mock.patch('arbol_root.groups.os.killpg') as send:
                self.assertFalse(force_group(PROCESS, clock.now, clock.pause))
            send.assert_not_called()

    def test_process_reader_failure_after_term_is_not_ended_without_another_signal(self) -> None:
        with self.simulated():
            with mock.patch('arbol_root.groups.members', side_effect=[{50:AT},ValueError('private unknown')]):
                with mock.patch('arbol_root.groups.os.killpg') as send:
                    clock = MovingClock()
                    with self.assertRaises(Refusal) as error:
                        force_group(PROCESS, clock.now, clock.pause)
        self.assertEqual(error.exception.code, 'not_ended')
        send.assert_called_once_with(50, signal.SIGTERM)


class NativeForce(unittest.TestCase):
    def setUp(self) -> None:
        self.f = Fixture(self)

    def check_mode(self, mode: str, expected: int) -> None:
        value = record(1)
        folder, child = self.f.live(value, mode)
        reply = self.f.cli('stop','--force',value['exchange'])
        self.assertEqual(reply.returncode, 0, reply.stderr)
        import json
        result = json.loads(reply.stdout)
        self.assertEqual((result['ended'],result['forced']), ('interrupted',True))
        self.assertEqual(result['settling'], {'exchange':value['exchange'],'settled':'interrupted'})
        self.assertEqual((folder / 'control').read_bytes(), b'')
        self.assertEqual(child.wait(timeout=5), -expected)
        self.assertEqual(members(child.pid), {})

    def test_private_group_that_obeys_term(self) -> None:
        """root.stop-force-term"""
        self.check_mode('term', signal.SIGTERM)

    def test_private_group_that_ignores_term_is_killed(self) -> None:
        """root.stop-force-kill"""
        self.check_mode('ignore', signal.SIGKILL)

    def test_ignored_child_is_killed_after_its_leader_exits(self) -> None:
        """root.stop-orphaned-child"""
        self.check_mode('child', signal.SIGTERM)

    def test_changed_record_and_unreadable_record_cannot_signal_a_replacement(self) -> None:
        """root.stop-record-refusal"""
        value = record(1)
        folder, child = self.f.live(value)
        expected = Observed(value['process'], True, None)
        with mock.patch('arbol_root.stop.read_exchange', return_value=Observed(PROCESS,True,None)):
            with mock.patch('arbol_root.stop.force_group') as send:
                with self.assertRaises(Refusal):
                    clock = MovingClock()
                    force_end(self.f.context, value['exchange'], expected, clock.now, clock.pause)
            send.assert_not_called()
        (folder / 'record.json').write_text('{broken}')
        with mock.patch('arbol_root.stop.force_group') as send:
            with self.assertRaises(Refusal) as error:
                stop(self.f.context, value['exchange'], True)
        self.assertEqual(error.exception.code, 'root_unavailable')
        send.assert_not_called()
        self.assertIsNone(child.poll())
