"""Jensen helpers use disposable PostgreSQL, fictional rows and owned private clients only."""

from __future__ import annotations

import contextlib
import json
import os
import shlex
import subprocess
import sys
import tempfile
import threading
import unittest
from datetime import UTC, datetime
from pathlib import Path
from types import SimpleNamespace
from typing import Any, cast
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
sys.path.insert(0,str(ROOT/'roots/sapling/drills'))
from drill_support import DrillError, Inspector, Places, wait_for  # noqa: E402
from migration_support import (  # noqa: E402
    Command,
    Snapshot,
    SourceLock,
    client_folder,
    direct_psql,
    fingerprints,
    thaw_client,
)
from sapling_outage import stopped  # noqa: E402
from stopping_support import frozen  # noqa: E402
from trunk_drill_support import Exchange, Frame, processes  # noqa: E402

from scripts.migration_fixtures import CHATS, EXCHANGES, SPECIAL, seed  # noqa: E402
from scripts.sql_support import SqlLab, private_server  # noqa: E402


class MigrationHelpers(unittest.TestCase):
    scope: contextlib.ExitStack
    lab: SqlLab

    @classmethod
    def setUpClass(cls) -> None:
        cls.scope = contextlib.ExitStack()
        cls.lab = cls.scope.enter_context(private_server())

    @classmethod
    def tearDownClass(cls) -> None:
        cls.scope.close()

    def database(self, name: str) -> Inspector:
        self.lab.server.createdb(name)
        self.lab.run_file(name,ROOT/'contract/1/layout.sql')
        seed(self.lab.server,name)
        i = Inspector.__new__(Inspector)
        i.places = Places(self.lab.server.home,self.lab.server.home,self.lab.server.home)
        i.psql,i.address,i.environment = self.lab.tools['psql'],self.lab.server.url(name),self.lab.environment
        return i

    def test_repeatable_read_fingerprints_preserve_exact_text_numbers_and_order(self) -> None:
        """sapling.migration-fingerprint"""
        i = self.database('fingerprint')
        self.lab.run_file('fingerprint',ROOT/'roots/jensen/layout.sql')
        self.lab.server.execute('fingerprint',"UPDATE runs SET usage='{\"exact\":0.123456789012345678901234567890}'::jsonb")
        original = Snapshot(i,provenance=True).read()
        second = Snapshot(i,provenance=True).read()
        self.assertEqual(fingerprints(original),fingerprints(second))
        self.assertEqual(set(original['tables']),{'chats','exchanges','messages','tool_calls','runs','migrated_chats'})
        self.assertEqual(original['tables']['exchanges']['count'],4)
        self.assertIn(SPECIAL,original['tables']['messages']['rows'][0]['text'])
        self.assertIn('0.123456789012345678901234567890',original['tables']['runs']['encodedRows'][0])
        self.assertEqual(original['isolation'],'repeatable read')
        self.assertEqual(original['readOnly'],'on')
        self.lab.server.execute('fingerprint',"UPDATE messages SET text=text||' ' WHERE position=0")
        changed = Snapshot(i,provenance=True).read()
        self.assertNotEqual(fingerprints(original)['messages'],fingerprints(changed)['messages'])
        self.assertEqual(fingerprints(original)['runs'],fingerprints(changed)['runs'])

    def test_a_concurrent_transaction_never_splits_the_multi_table_snapshot(self) -> None:
        """sapling.migration-snapshot-consistency"""
        i = self.database('concurrent')
        self.lab.server.execute('concurrent',f"UPDATE chats SET title='v0' WHERE id='{CHATS[0]}'; "
            f"UPDATE messages SET text='v0' WHERE exchange_id='{EXCHANGES[0]}' AND position=0")
        ended = threading.Event()
        errors: list[BaseException] = []
        def writer() -> None:
            try:
                for number in range(12):
                    self.lab.server.execute('concurrent',f"UPDATE chats SET title='v{number}' "
                        f"WHERE id='{CHATS[0]}'; UPDATE messages SET text='v{number}' "
                        f"WHERE exchange_id='{EXCHANGES[0]}' AND position=0;")
                    if ended.wait(0.01):
                        break
            except BaseException as error:
                errors.append(error)
        thread = threading.Thread(target=writer)
        thread.start()
        try:
            for _ in range(6):
                value = Snapshot(i).read()['tables']
                title = next(x['title'] for x in value['chats']['rows'] if x['id'] == CHATS[0])
                message = next(x['text'] for x in value['messages']['rows']
                               if x['exchange_id'] == EXCHANGES[0] and x['position'] == 0)
                self.assertEqual(title,message)
        finally:
            ended.set()
            thread.join(timeout=10)
        self.assertFalse(thread.is_alive())
        self.assertEqual(errors,[])

    def private_command(self, i: Inspector, home: Path) -> Frame:
        (home/'bin').mkdir()
        (home/'work').mkdir()
        script = home/'command.py'
        args = [i.psql,'--no-psqlrc','--no-password','--set','ON_ERROR_STOP=1','--dbname',i.address,
                '--command','COPY (SELECT * FROM chats) TO STDOUT WITH (FORMAT binary)']
        script.write_text('import subprocess,json\n'
            'p=subprocess.run('+repr(args)+',capture_output=True,env='+repr(i.environment)+')\n'
            'print(json.dumps({"refused":p.returncode!=0}),flush=True)\n'
            'raise SystemExit(1 if p.returncode else 0)\n')
        executable = home/'bin/arbol-roots'
        executable.write_text('#!/bin/sh\nexec '+shlex.join([os.path.realpath(sys.executable),'-IB',str(script)])+' "$@"\n')
        executable.chmod(0o700)
        return cast(Frame,SimpleNamespace(places=Places(home,home/'bin',home),work=home/'work',evidence=home))

    def test_observed_owned_copy_is_frozen_thawed_and_its_lock_client_is_reaped(self) -> None:
        """sapling.migration-owned-copy"""
        i = self.database('ownedcopy')
        before = fingerprints(Snapshot(i).read())
        with tempfile.TemporaryDirectory(prefix='private migration ') as directory:
            home = Path(directory)
            frame = self.private_command(i,home)
            lock = SourceLock(i,home)
            command = Command(frame,['migrate','fictional'],'migration')
            identities = [lock.identity]
            try:
                blocked = wait_for(lock.blocked_copy,seconds=10,interval=0.1)
                self.assertIn(lock.backend,blocked['blockers'])
                child = wait_for(command.psql,seconds=5)
                identities.append(child)
                self.assertEqual(direct_psql(command.process.pid),child)
                self.assertEqual(client_folder(child),frame.work.resolve())
                with frozen(child,home/'freeze.json'):
                    self.assertIn('T',subprocess.check_output(['/bin/ps','-o','stat=','-p',str(child['pid'])],text=True))
                self.assertTrue(json.loads((home/'freeze.json').read_text())['thawed'])
            finally:
                command.close()
                lock.close()
            self.assertTrue(all(processes().get(x['pid']) != x for x in identities))
            self.assertEqual(fingerprints(Snapshot(i).read()),before)
            self.assertEqual(i.read("SELECT to_json(count(*)) FROM pg_stat_activity WHERE datname='ownedcopy'"),1)

    def test_frozen_source_copy_fails_after_private_shutdown_and_service_is_restored(self) -> None:
        """sapling.migration-private-outage"""
        i = self.database('privateoutage')
        before = fingerprints(Snapshot(i).read())
        with tempfile.TemporaryDirectory(prefix='private frozen migration ') as directory:
            home = Path(directory)
            frame = self.private_command(i,home)
            lock = SourceLock(i,home)
            command = Command(frame,['migrate','fictional'],'migration')
            try:
                wait_for(lock.blocked_copy,seconds=10,interval=0.1)
                child = wait_for(command.psql,seconds=5)
                with frozen(child,home/'freeze.json'):
                    with stopped(stop=self.lab.server.stop,restore=self.lab.server.start,
                                 healthy=self.lab.server.running,receipt=home/'restoration.json'):
                        thaw_client(child)
                        result = command.finish(status=1,seconds=10)
                        self.assertEqual(result['reply'],{'refused':True})
                self.assertTrue(json.loads((home/'restoration.json').read_text())['restored'])
                self.assertNotEqual(processes().get(child['pid']),child)
            finally:
                command.close()
                lock.close()
                if not self.lab.server.running():
                    self.lab.server.start()
            self.assertEqual(fingerprints(Snapshot(i).read()),before)

    def test_copy_judgment_checks_actual_private_sql_bytes_snapshot_and_provenance(self) -> None:
        """sapling.migration-copy-judgment"""
        from migration_drills import judge_copy
        source = self.database('copyjudge')
        self.lab.server.createdb('copytarget')
        self.lab.run_file('copytarget',ROOT/'contract/1/layout.sql')
        self.lab.run_file('copytarget',ROOT/'roots/jensen/layout.sql')
        before = Snapshot(source).read()
        began = datetime.now(UTC)
        with tempfile.TemporaryDirectory() as directory:
            self.lab.run_file('copytarget',ROOT/'roots/jensen/migrate.sql',single=False,cwd=Path(directory),
                              variables={'from_database':'copyjudge','from_root':'sapling'})
        ended = datetime.now(UTC)
        target = Inspector.__new__(Inspector)
        target.places,target.psql,target.environment = source.places,source.psql,source.environment
        target.address = self.lab.server.url('copytarget')
        copied = Snapshot(target,provenance=True).read()
        proof = judge_copy(before,copied,began,ended)
        self.assertEqual(proof['openExchanges'],[EXCHANGES[2]])
        self.assertEqual(proof['chats'],2)
        self.assertEqual(fingerprints(Snapshot(source).read()),fingerprints(before))
        import copy
        for kind in ['text','end','provenance','snapshot']:
            changed = copy.deepcopy(copied)
            if kind == 'text':
                changed['tables']['messages']['encodedRows'][0] += ' '
            elif kind == 'end':
                next(x for x in changed['tables']['exchanges']['rows'] if x['id'] == EXCHANGES[2])['state']='cancelled'
            elif kind == 'provenance':
                changed['tables']['migrated_chats']['rows'][0]['ended_through']=999
            else:
                for row in changed['tables']['migrated_chats']['rows']:
                    row['migrated_at']='2000-01-01T00:00:00+00:00'
            with self.subTest(kind=kind),self.assertRaises(DrillError):
                judge_copy(before,changed,began,ended)

    def test_source_lock_constructor_failure_cleans_its_private_client(self) -> None:
        """sapling.migration-lock-failure"""
        i = self.database('failedlock')
        with tempfile.TemporaryDirectory() as directory:
            with mock.patch('migration_support.select.select',return_value=([],[],[])):
                with self.assertRaises(DrillError):
                    SourceLock(i,Path(directory))
            self.assertEqual(i.read("SELECT to_json(count(*)) FROM pg_stat_activity WHERE datname='failedlock'"),1)


class Creation(unittest.TestCase):
    def test_second_root_creation_uses_three_merged_checks_and_never_migrates_or_readies(self) -> None:
        """sapling.second-root-creation"""
        from jensen_creation import make_jensen
        with tempfile.TemporaryDirectory(prefix='private second root ') as directory:
            home = Path(directory)
            places = Places(home,home/'bin',home/'evidence')
            (places.roots/'sapling').mkdir(parents=True)
            (places.roots/'sapling/root.json').write_text('source root bytes')
            (places.driver/'runs').mkdir(parents=True)
            source_settings = home/'.arbol/roots/sapling'
            source_settings.mkdir(parents=True)
            (source_settings/'settings.json').write_text('fictional settings 🌲')
            retained = [{'root':'sapling','status':'working','current':True}]
            created = {'root':'jensen','name':'Jensen Root','grewFrom':'sapling','rootContract':1,'status':'preparing'}
            built = {'root':'jensen','build':'4','status':'working','checks':[
                {'name':name,'passed':True} for name in ['unit','layout','migration']],
                'source':{'commit':'merged','branch':'main','uncommittedChanges':False}}
            calls = mock.Mock()
            did_create = False
            def command(program: str, *args: str, **kwargs: Any) -> Any:
                nonlocal did_create
                if program == 'arbol-root':
                    return {'exchanges':[],'unreadable':[]}
                if program == 'arbol-builds':
                    for name,source in [('chat-tables.sql','contract/1/layout.sql'),
                                        ('root-tables.sql','roots/jensen/layout.sql'),('migrate.sql','roots/jensen/migrate.sql')]:
                        target = home/'Library/Application Support/Arbol/builds/arbol-root/4/layout'/name
                        target.parent.mkdir(parents=True,exist_ok=True)
                        target.write_bytes((ROOT/source).read_bytes())
                    return built
                if args == ('list',):
                    return [*([created] if did_create else []),*retained]
                if args[:1] == ('show',):
                    return created
                if args[:1] == ('create',):
                    did_create = True
                    import shutil
                    shutil.copytree(source_settings,home/'.arbol/roots/jensen')
                    return created
                self.fail('Unexpected global mutation: '+str((program,args)))
            calls.run.side_effect = command
            inspector = mock.Mock()
            inspector.read.return_value = []
            with mock.patch('jensen_creation.Inspector',return_value=inspector),\
                    mock.patch('jensen_creation.Snapshot') as snapshot,\
                    mock.patch('jensen_creation.merged_source',return_value='merged'):
                snapshot.return_value.read.return_value = {'tables':{'chats':{'count':2,'sha256':'unchanged'}}}
                report = make_jensen(places,ROOT,commands=calls)
                self.assertTrue(report['passed'])
                self.assertTrue(report['ownerDatabaseEmpty'])
                self.assertEqual(report['rootBuild'],'4')
                self.assertTrue((Path(report['evidence'])/'created.json').exists())
                self.assertTrue((Path(report['evidence'])/'build.json').exists())
                calls.run.assert_any_call('arbol-builds','build','arbol-root','--root','jensen','--repo',str(ROOT),seconds=1200)
                calls.run.reset_mock()
                with self.assertRaisesRegex(DrillError,'existing state'):
                    make_jensen(places,ROOT,commands=calls)
                self.assertEqual(calls.run.call_count,1)


class RootOwnership(unittest.TestCase):
    def test_jensen_owned_commands_and_snapshots_never_fall_back_to_sapling(self) -> None:
        """sapling.migration-root-exchange"""
        with tempfile.TemporaryDirectory() as directory:
            home = Path(directory)
            frame = mock.Mock()
            frame.places = Places(home,home/'bin',home)
            frame.evidence,frame.work = home,home
            i = mock.Mock()
            with mock.patch('trunk_drill_support.Inspector',return_value=i):
                exchange = Exchange(frame,None,root='jensen')
            self.assertEqual(exchange.root,'jensen')
            self.assertEqual(exchange.folder,frame.places.roots/'jensen/exchanges'/exchange.id)
            args = exchange.arguments('private')
            index = args.index('--root')
            self.assertEqual(args[index+1],'jensen')
            frame.calls.run.return_value = {'exchanges':[{'exchange':exchange.id,'state':'running'}]}
            self.assertEqual(exchange.listing_state(),'running')
            frame.calls.run.assert_called_with('arbol-root','--root','jensen','list')
            with mock.patch('trunk_drill_support.snapshot',return_value={}) as snap:
                exchange.persisted()
                snap.assert_called_once_with(i,exchange.id)
            with self.assertRaises(DrillError):
                Exchange(frame,None,root='Uppercase')


class ContinuationJudgment(unittest.TestCase):
    @staticmethod
    def history() -> dict[str, Any]:
        return {'tables':{'chats':{'rows':[{'id':'chat'}]},'exchanges':{'rows':[
            {'id':'first','chat_id':'chat','number':1,'state':'completed','replaced_by':None},
            {'id':'second','chat_id':'chat','number':2,'state':'completed','replaced_by':None}]},
            'messages':{'rows':[{'exchange_id':'second','position':1,'role':'assistant','text':'later 🌲  '},
                {'exchange_id':'first','position':0,'role':'user','text':'verification word for this chat: pine123.'},
                {'exchange_id':'first','position':1,'role':'assistant','text':'pine123'},
                {'exchange_id':'second','position':0,'role':'user','text':'Remember it?'}]},
            'tool_calls':{'rows':[]}}}

    def test_saved_chat_history_has_exact_order_word_and_next_number_and_refuses_busy(self) -> None:
        """sapling.migration-history-judgment"""
        from migration_drills import chat_history
        value = self.history()
        history,number,word = chat_history(value,'chat')
        self.assertEqual((number,word),(3,'pine123'))
        self.assertEqual([x['text'] for x in history],['verification word for this chat: pine123.','pine123',
                                                     'Remember it?','later 🌲  '])
        value['tables']['exchanges']['rows'][1]['state']='open'
        with self.assertRaises(DrillError):
            chat_history(value,'chat')

    def test_usage_refusal_prevents_reservation_and_ambiguous_acceptance_is_counted_once(self) -> None:
        """sapling.migration-real-budget"""
        from migration_drills import continuation
        with tempfile.TemporaryDirectory() as directory:
            home = Path(directory)
            frame = mock.Mock()
            frame.places = Places(home,home/'bin',home)
            frame.evidence = home
            frame.root_exchange.return_value.id = 'owned-exchange'
            limited = {'state':'signed_in','outcome':'ok','windows':[{'usedPercent':100,'limitReached':True}]}
            frame.calls.run.return_value = limited
            with mock.patch('migration_drills.qualified'),mock.patch('migration_drills.original_chat',return_value='chat'),\
                    mock.patch('migration_drills.Inspector'),mock.patch('migration_drills.Snapshot') as snap,\
                    mock.patch('migration_drills.Budget') as budget, mock.patch('migration_drills.fingerprints',return_value={}):
                snap.return_value.read.return_value = self.history()
                with self.assertRaisesRegex(DrillError,'usage'):
                    continuation(frame,real=True)
                budget.return_value.reserve.assert_not_called()
                frame.root_exchange.return_value.start.assert_not_called()
                frame.evidence = home/'next-attempt'
                frame.calls.run.return_value = {'state':'signed_in','outcome':'ok','windows':[]}
                budget.return_value.status.return_value = {'remaining':6,'attempts':[]}
                frame.root_exchange.return_value.start.side_effect = DrillError('ambiguous acceptance')
                frame.root_exchange.return_value.persisted.return_value = {'exchange':None}
                with self.assertRaisesRegex(DrillError,'ambiguous acceptance'):
                    continuation(frame,real=True)
                budget.return_value.reserve.assert_called_once_with('owned-exchange','SYL-189')
                budget.return_value.finish.assert_called_once_with('owned-exchange','ambiguous',usage=None)
                frame.root_exchange.return_value.start.assert_called_once()


class ReadyJudgment(unittest.TestCase):
    def test_ready_changes_cleanup_root_only_from_observed_catalogue_even_after_ambiguous_reply(self) -> None:
        """sapling.migration-ready-judgment"""
        from migration_drills import ready
        for ambiguous in (False,True):
            with self.subTest(ambiguous=ambiguous),tempfile.TemporaryDirectory() as directory:
                home = Path(directory)
                frame = mock.Mock()
                frame.places = Places(home,home/'bin',home)
                frame.current = 'sapling'
                path = frame.places.roots/'jensen/root.json'
                path.parent.mkdir(parents=True)
                path.write_text('unchanged root bytes')
                def command(program: str, *args: str, broken: bool = ambiguous, **kwargs: Any) -> Any:
                    if args == ('ready','jensen'):
                        if broken:
                            raise DrillError('ambiguous ready reply')
                        return {'root':'jensen','status':'working'}
                    if program == 'arbol-roots' and args == ('list',):
                        return [{'root':'jensen','current':True}]
                    if program == 'arbol-root' and args == ('list',):
                        return {'root':'jensen','rootBuild':'4'}
                    if args == ('show','sapling'):
                        return {'root':'sapling','status':'working'}
                    if args == ('migrate','jensen') and kwargs.get('status') == 1:
                        return {'error':{'code':'invalid_input'}}
                    self.fail(str((program,args,kwargs)))
                frame.calls.run.side_effect = command
                with mock.patch('migration_drills.qualified'),mock.patch('migration_drills.preparing',return_value='4'),\
                        mock.patch('migration_drills.Inspector'),mock.patch('migration_drills.Snapshot') as snap:
                    snap.return_value.read.return_value = {'tables':{}}
                    if ambiguous:
                        with self.assertRaisesRegex(DrillError,'ambiguous ready reply'):
                            ready(frame)
                        frame.root_exchange.assert_not_called()
                    else:
                        proof = ready(frame)
                        self.assertEqual(proof['currentRoot'],'jensen')
                        frame.root_exchange.assert_called_once_with('sapling','R5')
                self.assertEqual(frame.current,'jensen')
