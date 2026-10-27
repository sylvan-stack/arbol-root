"""The installed-drill frame's private boundaries, without any owner Root or inference."""

from __future__ import annotations

import json
import os
import signal
import subprocess
import sys
import tempfile
import unittest
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'roots/sapling/drills'))
from drill_support import DrillError  # noqa: E402
from trunk_drill_support import StandinHome, existing_rows_unchanged, processes, verify_process  # noqa: E402
from trunk_drills import run_drill  # noqa: E402


class PrivateDriver(unittest.TestCase):
    def setUp(self) -> None:
        temporary = tempfile.TemporaryDirectory(prefix='private-drill-fixture-')
        self.addCleanup(temporary.cleanup)
        self.home = Path(temporary.name)
        self.launcher = self.home/'installed-trunk'
        self.launcher.write_text('#!/bin/sh\nexit 7\n')
        self.launcher.chmod(0o700)
        self.fixture = StandinHome(self.launcher,'selftest plain')
        self.addCleanup(self.fixture.close)

    def test_copied_launcher_and_actual_standin_use_only_the_private_home(self) -> None:
        """sapling.standin-isolation"""
        self.assertEqual((self.fixture.bin/'arbol-trunk').read_bytes(),self.launcher.read_bytes())
        self.assertNotEqual(self.fixture.home,self.home)
        wrapper = self.fixture.bin/'arbol-claude-driver'
        before = set(self.home.rglob('*'))
        response = subprocess.run([str(wrapper),'info'],capture_output=True,text=True,check=True,
                                  env={'HOME':str(self.home),'PATH':'/unusable','ARBOL_TEST_TIME_SCALE':'nan'},timeout=10)
        info = json.loads(response.stdout)
        self.assertTrue(Path(info['stateDirectory']).is_relative_to(self.fixture.home))
        self.assertEqual(info['driver'],'claude')
        self.assertEqual(set(self.home.rglob('*')),before)
        records = self.fixture.records()
        self.assertEqual(records[0]['arguments'],['info'])
        self.assertEqual(records[0]['request'],None)

    def test_actual_script_output_and_request_are_recorded_without_owner_state(self) -> None:
        """sapling.standin-script"""
        request = self.home/'request.json'
        value = {'input':'Hello','subscriptionId':'standin','model':'standin-model','runId':'private-drill-run'}
        request.write_text(json.dumps(value))
        response = subprocess.run([str(self.fixture.bin/'arbol-claude-driver'),'run','--request',str(request)],
                                  capture_output=True,text=True,timeout=10,check=True)
        lines = [json.loads(line) for line in response.stdout.splitlines()]
        self.assertEqual(lines[-1]['outcome'],'completed')
        self.assertEqual(self.fixture.records()[0]['request'],value)
        self.assertFalse((self.home/'Library').exists())
        self.assertFalse((self.home/'.arbol').exists())

    def test_scenario_release_and_finish_are_owned_and_reset_between_uses(self) -> None:
        """sapling.standin-controls"""
        self.fixture.release()
        self.fixture.release(finish=True)
        self.fixture.part('R12 middle')
        self.assertFalse((self.fixture.home/'standin/release').exists())
        self.assertFalse((self.fixture.home/'standin/finish').exists())
        self.assertEqual((self.fixture.home/'standin/scenario').read_text(),'R12 middle\n')


class ProcessAndRows(unittest.TestCase):
    def test_live_private_process_identity_is_checked_before_a_signal(self) -> None:
        """sapling.drill-process-identity"""
        child = subprocess.Popen(['/bin/sleep','30'],start_new_session=True)
        try:
            actual = processes()[child.pid]
            record = {'process':{'pid':child.pid,'startedAt':actual['started'].isoformat()}}
            self.assertEqual(verify_process(record)['pid'],child.pid)
            record['process']['startedAt'] = (actual['started']-timedelta(days=1)).isoformat()
            with self.assertRaisesRegex(DrillError,'start identity changed'):
                verify_process(record)
            self.assertIsNone(child.poll())
            self.assertEqual(os.getpgid(child.pid),child.pid)
        finally:
            child.send_signal(signal.SIGTERM)
            child.wait(timeout=5)

    def test_missing_nonleader_and_own_group_refuse_without_signalling(self) -> None:
        """sapling.drill-process-refusal"""
        started = datetime.now(UTC)
        for pid,group in [(123,124),(os.getpgrp(),os.getpgrp())]:
            record = {'process':{'pid':pid,'startedAt':started.isoformat()}}
            with self.subTest(pid=pid),self.assertRaises(DrillError):
                verify_process(record,{pid:{'pid':pid,'group':group,'started':started}})
        with self.assertRaises(DrillError):
            verify_process({'process':{'pid':123,'startedAt':started.isoformat()}},{})

    def test_new_rows_are_allowed_but_changing_or_dropping_old_rows_refuses(self) -> None:
        """sapling.drill-existing-rows"""
        before: dict[str,Any] = {'messages':[{'exchange_id':'old','text':'keep it'}],
                                 'runs':[{'usage':{'inputTokens':2}}]}
        after = {**before,'messages':[*before['messages'],{'exchange_id':'new','text':'new drill'}]}
        self.assertTrue(existing_rows_unchanged(before,after))
        for bad in [[],[{'exchange_id':'old','text':'changed'}]]:
            self.assertFalse(existing_rows_unchanged(before,{**after,'messages':bad}))

    def test_failed_drill_still_closes_frame_and_saves_its_failure(self) -> None:
        """sapling.drill-failure-cleanup"""
        with tempfile.TemporaryDirectory() as directory:
            frame: Any = mock.Mock()
            frame.evidence = Path(directory)
            with mock.patch('trunk_drills.Frame',return_value=frame),\
                    mock.patch.dict('trunk_drills.DRILLS',{'test':mock.Mock(side_effect=DrillError('test failure'))}):
                with self.assertRaisesRegex(DrillError,'test failure'):
                    run_drill('test')
            frame.close.assert_called_once_with()
            self.assertEqual(json.loads((frame.evidence/'failure.json').read_text())['error'],'test failure')

    def test_real_variant_is_refused_for_every_other_drill_before_frame_creation(self) -> None:
        """sapling.drill-real-boundary"""
        with mock.patch('trunk_drills.Frame') as frame:
            with self.assertRaises(DrillError):
                run_drill('trunk-hangs',real=True)
            frame.assert_not_called()
