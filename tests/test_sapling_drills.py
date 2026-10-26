"""First Roots drill helpers use private state and their own PostgreSQL server."""

from __future__ import annotations

import json
import stat
import subprocess
import sys
import tempfile
import unittest
import uuid
from pathlib import Path
from typing import Any
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT / 'roots/sapling/drills'))
sys.path.insert(0,str(ROOT / 'contract/conformance'))
from drill_support import Budget, Commands, DrillError, Inspector, Places, new_json, wait_for  # noqa: E402
from rct_conformance.postgres import Server  # noqa: E402
from sapling_creation import make_sapling  # noqa: E402
from sapling_messages import judge, real_messages  # noqa: E402


class Frame(unittest.TestCase):
    def setUp(self) -> None:
        temporary = tempfile.TemporaryDirectory(prefix="private sapling drill '")
        self.addCleanup(temporary.cleanup)
        self.home = Path(temporary.name).resolve()
        self.places = Places(self.home,self.home/'bin',self.home/'evidence')
        self.places.bin.mkdir()

    def test_receipts_are_private_and_never_overwrite_an_earlier_attempt(self) -> None:
        """sapling.receipt"""
        path = self.places.evidence/'request.json'
        new_json(path,{'message':'fictional 🌲'})
        self.assertEqual(stat.S_IMODE(path.stat().st_mode),0o600)
        with self.assertRaises(FileExistsError):
            new_json(path,{'message':'must not replace'})
        self.assertEqual(json.loads(path.read_text())['message'],'fictional 🌲')

    def test_json_commands_preserve_arguments_and_reject_bad_status_or_non_json(self) -> None:
        """sapling.commands"""
        program = self.places.bin/'reply'
        program.write_text(f'#!{sys.executable} -I\nimport json,sys\nprint(json.dumps(sys.argv[1:]))\n')
        program.chmod(0o755)
        args = ['one two',"a'b",'$HOME','🌲']
        self.assertEqual(Commands(self.places,login=False).run('reply',*args),args)
        program.write_text('#!/bin/sh\nprintf not-json\n')
        with self.assertRaises(DrillError):
            Commands(self.places,login=False).run('reply')
        program.write_text('#!/bin/sh\nexit 3\n')
        with self.assertRaisesRegex(DrillError,'returned 3'):
            Commands(self.places,login=False).run('reply')

    def test_wait_has_a_deadline_and_never_retries_after_that_deadline(self) -> None:
        """sapling.wait"""
        moment = [0.0]
        calls = []
        def probe() -> None:
            calls.append(moment[0])
        def pause(delay: float) -> None:
            moment[0] += delay
        with self.assertRaises(DrillError):
            wait_for(probe,seconds=1,interval=0.3,clock=lambda:moment[0],pause=pause)
        self.assertEqual(moment[0],1)
        self.assertLessEqual(max(calls),1)

    def test_budget_reserves_before_submission_caps_ten_and_never_replays_an_exchange(self) -> None:
        """sapling.budget"""
        budget = Budget(self.places.evidence)
        exchanges = [str(uuid.uuid4()) for _ in range(10)]
        for exchange in exchanges:
            budget.reserve(exchange)
        self.assertEqual(budget.status()['remaining'],0)
        with self.assertRaises(DrillError):
            budget.reserve(str(uuid.uuid4()))
        with self.assertRaises(DrillError):
            budget.reserve(exchanges[0])
        budget.finish(exchanges[0],'completed',usage={'costUSD':0.001})
        self.assertEqual(budget.status()['usedOrReserved'],10)
        with self.assertRaises(DrillError):
            budget.finish(exchanges[0],'no_vendor')
        budget.finish(exchanges[1],'no_vendor')
        budget.reserve(str(uuid.uuid4()),'SYL-187')
        self.assertEqual(budget.status()['remaining'],0)

    def test_torn_or_unknown_budget_history_refuses_new_spending(self) -> None:
        """sapling.budget-refusal"""
        folder = self.places.evidence
        folder.mkdir()
        journal = folder/'live-message-budget.jsonl'
        for content in ['{"version":1', '{"version":2}\n', 'not-json\n']:
            journal.write_text(content)
            with self.subTest(content=content),self.assertRaises(DrillError):
                Budget(folder).reserve(str(uuid.uuid4()))

    def test_two_processes_cannot_both_spend_the_last_available_message(self) -> None:
        """sapling.budget-concurrent"""
        budget = Budget(self.places.evidence)
        for _ in range(9):
            budget.reserve(str(uuid.uuid4()))
        code = ("import sys;sys.path.insert(0,"+repr(str(ROOT/'roots/sapling/drills'))+")\n"
                "from drill_support import Budget,DrillError\nfrom pathlib import Path\n"
                "try: Budget(Path(sys.argv[1])).reserve(sys.argv[2])\n"
                "except DrillError: sys.exit(1)\n")
        children = [subprocess.Popen([sys.executable,'-I','-B','-c',code,str(self.places.evidence),str(uuid.uuid4())],
                                     stdout=subprocess.PIPE,stderr=subprocess.PIPE) for _ in range(2)]
        try:
            for child in children:
                child.communicate(timeout=5)
            self.assertEqual(sorted(child.returncode for child in children),[0,1])
            self.assertEqual(budget.status()['usedOrReserved'],10)
        finally:
            for child in children:
                if child.poll() is None:
                    child.kill()
                child.communicate(timeout=5)


class ReadOnly(unittest.TestCase):
    def test_inspection_uses_its_private_server_and_cannot_write(self) -> None:
        """sapling.read-only"""
        with tempfile.TemporaryDirectory(prefix='sapling inspector ') as temporary:
            home = Path(temporary).resolve()
            places = Places(home,home/'bin',home/'evidence')
            server = Server.create(home/'postgres',home=home)
            try:
                server.createdb('fictional')
                server.execute('fictional','CREATE TABLE notes(value integer); INSERT INTO notes VALUES (1); '
                               'CREATE SEQUENCE probe_seq;')
                root = places.roots/'sapling'
                root.mkdir(parents=True)
                new_json(root/'root.json',{'root':'sapling','rootContract':1,'database':'fictional'})
                new_json(home/'.arbol/database.json',{'address':server.address})
                security = home/'no-credential'
                security.write_text('#!/bin/sh\nexit 44\n')
                security.chmod(0o755)
                inspector = Inspector(places,psql=server.tools['psql'],security=str(security))
                self.assertEqual(inspector.read('SELECT json_agg(value) FROM notes'),[1])
                with self.assertRaises(DrillError):
                    inspector.read('DELETE FROM notes')
                with self.assertRaises(DrillError):
                    inspector.read('SELECT 1; DELETE FROM notes')
                with self.assertRaises(DrillError):
                    inspector.read("SELECT nextval('probe_seq')")
                self.assertFalse(server.value('fictional','SELECT to_json(is_called) FROM probe_seq'))
                self.assertEqual(server.value('fictional','SELECT count(*) FROM notes'),1)
                self.assertEqual(set(inspector.environment),{'HOME','PATH','LANG'})
            finally:
                server.remove()


class Creation(unittest.TestCase):
    def setUp(self) -> None:
        temporary = tempfile.TemporaryDirectory(prefix='private sapling creation ')
        self.addCleanup(temporary.cleanup)
        self.home = Path(temporary.name).resolve()
        self.places = Places(self.home,self.home/'bin',self.home/'evidence')
        self.calls = mock.Mock(spec=Commands)
        self.inspector = mock.Mock(spec=Inspector)
        self.inspector.counts.return_value = dict.fromkeys(['chats','exchanges','messages','tool_calls','runs'],0)

    def replies(self) -> list[object]:
        return [[], {'root':'sapling','name':'First Sapling','status':'preparing','rootContract':1},
                {'root':'sapling','build':'1','status':'working',
                 'checks':[{'name':name,'passed':True} for name in ['unit','layout','migration']],
                 'source':{'commit':'merged-source','branch':'main','uncommittedChanges':False}},
                {'root':'sapling','rootBuild':'1','files':['chat-tables.sql','root-tables.sql']},
                {'root':'sapling','status':'working'}, [{'root':'sapling','current':True}],
                {'root':'sapling','rootBuild':'1','exchanges':[],'unreadable':[]}]

    def test_creation_runs_the_named_steps_and_preserves_receipts(self) -> None:
        """sapling.creation"""
        self.calls.run.side_effect = self.replies()
        with mock.patch('sapling_creation.merged_source',return_value='merged-source'):
            result = make_sapling(self.places,self.home/'readonly',commands=self.calls,
                                  inspector=lambda _places:self.inspector)
        self.assertTrue(result['current'])
        actual = [call.args[:2] for call in self.calls.run.call_args_list]
        self.assertEqual(actual,[('arbol-roots','list'),('arbol-roots','create'),('arbol-builds','build'),
                                 ('arbol-roots','migrate'),('arbol-roots','ready'),('arbol-roots','list'),
                                 ('arbol-root','--root')])
        self.assertEqual(len(list(Path(result['receipt']).glob('*.json'))),6)
        self.assertEqual(result['vendorRequests'],0)

    def test_existing_or_unpublished_root_is_never_migrated_or_removed(self) -> None:
        """sapling.creation-refusal"""
        for existing in ['catalogue','folder','settings']:
            self.calls.reset_mock()
            self.calls.run.side_effect = [[{'root':'sapling'}] if existing == 'catalogue' else []]
            target = self.places.roots/'sapling' if existing == 'folder' else self.home/'.arbol/roots/sapling'
            if existing != 'catalogue':
                target.mkdir(parents=True)
            with self.subTest(existing=existing),self.assertRaises(DrillError):
                make_sapling(self.places,self.home/'readonly',commands=self.calls)
            self.assertEqual(self.calls.run.call_count,1)
            if existing != 'catalogue':
                target.rmdir()

    def test_failed_build_stops_before_migration_and_keeps_created_receipt(self) -> None:
        """sapling.creation-failure"""
        replies = self.replies()
        replies[2] = {'root':'sapling','status':'failed'}
        self.calls.run.side_effect = replies
        with mock.patch('sapling_creation.merged_source',return_value='merged-source'):
            with self.assertRaises(DrillError):
                make_sapling(self.places,self.home/'readonly',commands=self.calls)
        self.assertEqual(self.calls.run.call_count,3)
        receipts = list((self.places.evidence/'creation-attempts').iterdir())
        self.assertEqual(len(receipts),1)
        self.assertTrue((receipts[0]/'created.json').is_file())
        self.assertEqual(json.loads((receipts[0]/'failure.json').read_text())['phase'],'build')

    def test_branch_source_is_refused_before_create(self) -> None:
        """sapling.creation-source"""
        self.calls.run.return_value = []
        with mock.patch('sapling_creation.merged_source',side_effect=DrillError('unmerged source')):
            with self.assertRaises(DrillError):
                make_sapling(self.places,self.home/'branch',commands=self.calls)
        self.assertEqual(self.calls.run.call_count,1)
        self.assertFalse(self.places.evidence.exists())


class MessageCommands(Commands):
    def __init__(self, places: Places, *, fail_start: bool = False) -> None:
        super().__init__(places,login=False)
        self.fail_start = fail_start
        self.starts = 0
        self.requests: list[dict[str, Any]] = []
        self.chat = str(uuid.uuid4())

    def run(self, program: str, *arguments: str, **options: Any) -> Any:
        if program == 'arbol-roots':
            return {'root':'sapling','status':'working'}
        if program == 'arbol-claude-driver':
            return {'state':'signed_in'} if 'check' in arguments else {
                'outcome':'ok','windows':[{'kind':'session','usedPercent':0,'limitReached':False}]}
        if 'start' in arguments:
            self.starts += 1
            if self.fail_start:
                raise DrillError('ambiguous acceptance')
            request = Path(arguments[arguments.index('--request')+1])
            value = json.loads(request.read_text())
            exchange = arguments[arguments.index('--exchange')+1]
            self.requests.append({'request':value,'arguments':arguments,'exchange':exchange})
            request.unlink()
            return {'accepted':True,'duplicate':False,'root':'sapling','exchange':exchange,'chat':self.chat,
                    'number':self.starts,'trunk':'trivial','build':'3'}
        return {'exchanges':[{'exchange':self.requests[-1]['exchange'],'state':'running'}] if self.requests else [],
                'unreadable':[]}

    def data(self) -> dict[str, Any]:
        last = self.requests[-1]
        word = self.requests[0]['request']['message'].split('chat: ')[1].split('.')[0]
        answer = 'remembered' if len(self.requests) == 1 else word
        return {'exchange':{'id':last['exchange'],'chat_id':self.chat,'number':len(self.requests),'state':'completed',
                            'trunk':'trivial','build':'3','route':last['request']['route']},
                'messages':[{'position':0,'role':'user','text':last['request']['message']},
                            {'position':1,'role':'assistant','text':answer}],
                'runs':[{'outcome':'completed','usage':{'inputTokens':10,'outputTokens':3,'costUSD':0.001}}]}


class Messages(unittest.TestCase):
    def setUp(self) -> None:
        temporary = tempfile.TemporaryDirectory(prefix='private sapling messages ')
        self.addCleanup(temporary.cleanup)
        home = Path(temporary.name).resolve()
        self.places = Places(home,home/'bin',home/'evidence')
        self.calls = MessageCommands(self.places)
        self.inspector = mock.Mock(spec=Inspector)
        self.inspector.read.side_effect = lambda _sql:self.calls.data()
        self.inspector.counts.return_value = {'chats':1,'exchanges':2,'messages':4,'runs':2,'tool_calls':0}

    def test_preflight_does_not_submit_and_two_explicit_submissions_keep_the_same_chat(self) -> None:
        """sapling.messages"""
        preflight = real_messages(self.places,commands=self.calls)
        self.assertTrue(preflight['preflightOnly'])
        self.assertEqual(self.calls.starts,0)
        result = real_messages(self.places,send=True,commands=self.calls,inspector=self.inspector)
        self.assertEqual(result['submissions'],2)
        self.assertEqual(result['budget']['remaining'],8)
        self.assertEqual(result['reportedCostUSD'],'0.002')
        self.assertEqual([item['number'] for item in result['messages']],[1,2])
        self.assertNotIn('--chat',self.calls.requests[0]['arguments'])
        self.assertIn('--chat',self.calls.requests[1]['arguments'])
        self.assertTrue(result['messages'][1]['remembered'])

    def test_ambiguous_start_counts_and_is_never_automatically_retried(self) -> None:
        """sapling.messages-ambiguous"""
        self.calls.fail_start = True
        with self.assertRaisesRegex(DrillError,'ambiguous acceptance'):
            real_messages(self.places,send=True,commands=self.calls,inspector=self.inspector)
        self.assertEqual(self.calls.starts,1)
        status = Budget(self.places.evidence).status()
        self.assertEqual(status['usedOrReserved'],1)
        self.assertEqual(status['attempts'][0]['state'],'ambiguous')

    def test_no_two_message_allowance_means_no_submission(self) -> None:
        """sapling.messages-allowance"""
        for _ in range(9):
            Budget(self.places.evidence).reserve(str(uuid.uuid4()))
        with self.assertRaises(DrillError):
            real_messages(self.places,send=True,commands=self.calls,inspector=self.inspector)
        self.assertEqual(self.calls.starts,0)

    def test_reached_or_unavailable_usage_never_submits(self) -> None:
        """sapling.messages-usage"""
        original = self.calls.run
        reports: list[dict[str,Any]] = [{'outcome':'unavailable','windows':[]},
                                       {'outcome':'ok','windows':[{'limitReached':True}]},
                                       {'outcome':'ok','windows':[{'usedPercent':100}]}]
        for report in reports:
            def run(program: str, *args: str, selected: dict[str, Any] = report, **options: Any) -> Any:
                if program == 'arbol-claude-driver' and 'usage' in args:
                    return selected
                return original(program,*args,**options)
            with mock.patch.object(self.calls,'run',side_effect=run):
                with self.assertRaises(DrillError):
                    real_messages(self.places,send=True,commands=self.calls,inspector=self.inspector)
        self.assertEqual(self.calls.starts,0)

    def test_judgement_refuses_lost_history_wrong_route_or_missing_usage(self) -> None:
        """sapling.messages-judgement"""
        request = self.places.evidence/'request.json'
        new_json(request,{'message':'Remember this word for this chat: pinefixture. Reply remembered.',
                          'route':{'driver':'claude','subscription':'anthropic','model':'haiku'}})
        accepted = self.calls.run('arbol-root','start','--exchange',str(uuid.uuid4()),'--request',str(request))
        good = self.calls.data()
        for case in ['word','route','tokens']:
            data = json.loads(json.dumps(good))
            if case == 'route':
                data['exchange']['route']['model'] = 'other'
            elif case == 'tokens':
                data['runs'][0]['usage'] = {}
            with self.subTest(case=case),self.assertRaises(DrillError):
                judge(data,accepted,self.calls.requests[0]['request']['message'],1,
                      remembered='not-the-remembered-word' if case == 'word' else None)
