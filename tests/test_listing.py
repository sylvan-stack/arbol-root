from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))
from arbol_root import listing as records  # noqa: E402
from arbol_root.listing import listing  # noqa: E402
from arbol_root.model import Identity, Refusal  # noqa: E402
from arbol_root.process import process_alive, started_at  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
AT = '2026-10-26T09:00:00.000Z'
CHAT = 'c3d4e5f6-0718-4293-a4b5-c6d7e8f90a1b'


def record(number: int, *, root: str = 'sapling', pid: int = 123, accepted: bool = True, ended: bool = False) -> dict[str, Any]:
    value = {'rootContract':1,'root':root,'exchange':f'00000000-0000-4000-8000-{number:012d}',
             'chat':CHAT,'trunk':'trivial','build':'a','process':{'pid':pid,'startedAt':AT},
             'signsOfLife':{'heartbeat':41,'waitingFor':'tool','since':AT}}
    if accepted:
        value['acceptedAt'] = AT
    if ended:
        value['end'] = {'state':'completed','at':AT}
    return value


class Listing(unittest.TestCase):
    def setUp(self) -> None:
        temporary = tempfile.TemporaryDirectory(prefix='rtm-list-')
        self.addCleanup(temporary.cleanup)
        self.base = Path(temporary.name).resolve()
        self.root = self.base / 'root'
        self.root.mkdir()
        (self.root / 'root.json').write_text('{"root":"sapling"}')
        self.catalogue = self.root / 'exchanges'
        self.catalogue.mkdir()
        self.context = Identity('sapling','7','1.0.0',self.root,self.base / 'no-launcher')

    def put(self, value: dict[str, Any]) -> Path:
        folder = self.catalogue / str(value['exchange'])
        folder.mkdir(exist_ok=True)
        (folder / 'record.json').write_text(json.dumps(value))
        return folder

    def test_all_six_states_are_read_from_records_alone_in_deterministic_order(self) -> None:
        """root.list-states"""
        cases = [(False,False,True,'accepting'), (False,False,False,'unaccepted'),
                 (True,False,True,'running'), (True,True,True,'ending'),
                 (True,True,False,'unsaved'), (True,False,False,'interrupted')]
        for i,(accepted,ended,alive,_state) in reversed(list(enumerate(cases, 1))):
            folder = self.put(record(i,accepted=accepted,ended=ended,pid=123 if alive else 456))
            for name in ['events.jsonl','control','request.json']:
                os.mkfifo(folder / name)
        (self.catalogue / '.unfinished.new').mkdir()
        (self.catalogue / 'ordinary-file').write_text('skip')
        os.mkfifo(self.catalogue / 'ordinary-fifo')
        with mock.patch('arbol_root.process.started_at',side_effect=lambda pid:datetime(2026,10,26,9,tzinfo=UTC) if pid==123 else None):
            answer = listing(self.context)
        self.assertEqual(answer['rootBuild'], '7')
        self.assertEqual(answer['rootPackageVersion'], '1.0.0')
        self.assertEqual([item['state'] for item in answer['exchanges']], [case[3] for case in cases])
        self.assertEqual(answer['unreadable'], [])
        self.assertTrue(all(item['root']=='sapling' for item in answer['exchanges']))
        self.assertFalse((self.base / 'no-launcher').exists())

    def test_unknown_values_are_kept_unknown_fields_ignored_and_end_errors_whole(self) -> None:
        """root.list-forward-compatible"""
        value = record(1, ended=True)
        value['signsOfLife']['waitingFor'] = 'future-wait'
        value['signsOfLife']['future'] = 3
        value['end'] = {'state':'future-end','at':AT,'error':{'code':'x','message':'failed','retryAfterSeconds':12}}
        value['future'] = {'private':'ignored'}
        self.put(value)
        with mock.patch('arbol_root.process.started_at',return_value=None):
            item = listing(self.context)['exchanges'][0]
        self.assertEqual(item['signsOfLife']['waitingFor'], 'future-wait')
        self.assertNotIn('future', item['signsOfLife'])
        self.assertNotIn('future', item)
        self.assertEqual(item['end'], value['end'])

    def test_missing_malformed_fifo_symlink_records_are_isolated_without_following(self) -> None:
        """root.list-unreadable"""
        expected = []
        for i,kind in enumerate(['missing','json','fifo','symlink'], 1):
            folder = self.put(record(i))
            path = folder / 'record.json'
            path.unlink()
            if kind == 'json':
                path.write_text('{bad}')
            elif kind == 'fifo':
                os.mkfifo(path)
            elif kind == 'symlink':
                target = self.base / 'outside-record'
                target.write_text(json.dumps(record(i)))
                path.symlink_to(target)
            expected.append(folder.name)
        link = self.catalogue / 'symlink-directory'
        link.symlink_to(self.base, target_is_directory=True)
        expected.append(link.name)
        answer = listing(self.context)
        self.assertEqual(answer['exchanges'], [])
        self.assertEqual(answer['unreadable'], sorted(expected))

    def test_bad_record_fields_and_process_check_failure_are_unreadable(self) -> None:
        """root.list-record-validation"""
        original = record(1)
        folder = self.put(original)
        variants: list[dict[str, Any]] = [{'root':'other'}, {'exchange':CHAT}, {'chat':'not-uuid'}, {'rootContract':True},
                    {'build':'../x'}, {'process':{'pid':True,'startedAt':AT}},
                    {'process':{'pid':123,'startedAt':'not-time'}},
                    {'signsOfLife':{'heartbeat':-1,'waitingFor':'tool','since':AT}}, {'acceptedAt':None},
                    {'end':{'state':'failed','at':AT,'error':[]}}]
        for change in variants:
            with self.subTest(change=change):
                (folder / 'record.json').write_text(json.dumps({**original,**change}))
                self.assertEqual(listing(self.context)['unreadable'], [folder.name])
        (folder / 'record.json').write_text(json.dumps(original))
        with mock.patch('arbol_root.process.started_at',side_effect=ValueError('private ps refusal')):
            self.assertEqual(listing(self.context)['unreadable'], [folder.name])
        (folder / 'record.json').write_text(json.dumps(original).replace('"heartbeat": 41','"heartbeat": NaN'))
        self.assertEqual(listing(self.context)['unreadable'], [folder.name])

    def test_directory_gone_before_record_read_is_left_out_and_missing_record_is_unreadable(self) -> None:
        """root.list-disappearance"""
        folder = self.put(record(1))
        reader = records.read_record
        def disappear(catalogue: int, name: str) -> dict[str, Any]:
            shutil.rmtree(folder)
            return reader(catalogue,name)
        with mock.patch('arbol_root.listing.read_record',side_effect=disappear):
            self.assertEqual(listing(self.context), {'root':'sapling','rootBuild':'7','rootPackageVersion':'1.0.0',
                                                    'exchanges':[],'unreadable':[]})
        folder.mkdir()
        self.assertEqual(listing(self.context)['unreadable'], [folder.name])

    def test_missing_catalogue_is_empty_but_file_symlink_or_enumeration_error_refuses(self) -> None:
        """root.list-catalogue"""
        self.catalogue.rmdir()
        self.assertEqual(listing(self.context)['exchanges'], [])
        for kind in ['file','symlink']:
            with self.subTest(kind=kind):
                if kind == 'file':
                    self.catalogue.write_text('not a directory')
                else:
                    self.catalogue.symlink_to(self.base, target_is_directory=True)
                with self.assertRaises(Refusal) as error:
                    listing(self.context)
                self.assertEqual(error.exception.code, 'root_unavailable')
                self.catalogue.unlink()
        self.catalogue.mkdir()
        with mock.patch('arbol_root.listing.os.scandir',side_effect=PermissionError('private fixture')):
            with self.assertRaises(Refusal) as error:
                listing(self.context)
        self.assertEqual(error.exception.code, 'root_unavailable')

    def test_cli_lists_with_own_identity_and_no_launcher_settings_or_payload_access(self) -> None:
        """root.list-boundary"""
        settings = self.base / '.arbol'
        settings.mkdir()
        os.mkfifo(settings / 'database.json')
        env = {**os.environ,'HOME':str(self.base),'ARBOL_BUILD_NUMBER':'ffff','TZ':'Pacific/Honolulu'}
        reply = subprocess.run([sys.executable,'-I','-B',str(ROOT / 'bin/entry.py'),'--root','sapling','list',
                                '--root-dir',str(self.root),'--bin-dir',str(self.base / 'no-launcher')],
                               env=env, capture_output=True, check=True, timeout=5)
        value = json.loads(reply.stdout)
        expected = json.loads((ROOT / 'build.json').read_text())['build'] if (ROOT / 'build.json').exists() else '0'
        self.assertEqual(value, {'root':'sapling','rootBuild':expected,'rootPackageVersion':'1.0.0',
                                'exchanges':[],'unreadable':[]})


class ProcessIdentity(unittest.TestCase):
    def test_native_live_gone_and_reused_pid_identity(self) -> None:
        """root.list-process"""
        actual = started_at(os.getpid())
        assert actual is not None
        self.assertTrue(process_alive({'pid':os.getpid(),'startedAt':actual.isoformat()}))
        self.assertFalse(process_alive({'pid':os.getpid(),'startedAt':(actual+timedelta(seconds=10)).isoformat()}))
        child = subprocess.Popen([sys.executable,'-I','-B','-c','pass'])
        child.wait(timeout=5)
        self.assertFalse(process_alive({'pid':child.pid,'startedAt':actual.isoformat()}))

    def test_clean_c_utc_ps_environment_and_two_second_tolerance(self) -> None:
        """root.list-process-environment"""
        actual = subprocess.CompletedProcess([],0,'Mon Oct 26 09:00:00 2026\n','')
        with (mock.patch.dict(os.environ, {'PGPASSWORD':'fictional','TZ':'Pacific/Honolulu','LANG':'es_ES.UTF-8'}),
              mock.patch('arbol_root.process.subprocess.run',return_value=actual) as ps):
            self.assertTrue(process_alive({'pid':123,'startedAt':'2026-10-26T09:00:02.000Z'}))
            self.assertFalse(process_alive({'pid':123,'startedAt':'2026-10-26T09:00:02.001Z'}))
        self.assertEqual(ps.call_args.args[0], ['/bin/ps','-o','lstart=','-p','123'])
        self.assertEqual(ps.call_args.kwargs['env'], {'PATH':'/usr/bin:/bin','LANG':'C','LC_ALL':'C','TZ':'UTC'})
        self.assertEqual(ps.call_args.kwargs['timeout'], 5)
        for process in [{'pid':True,'startedAt':AT}, {'pid':0,'startedAt':AT}, {'pid':123,'startedAt':'2026-10-26'}]:
            with self.subTest(process=process), self.assertRaises(ValueError):
                process_alive(process)
