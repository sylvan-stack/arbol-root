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

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT / 'roots/sapling/drills'))
sys.path.insert(0,str(ROOT / 'contract/conformance'))
from drill_support import Budget, Commands, DrillError, Inspector, Places, new_json, wait_for  # noqa: E402
from rct_conformance.postgres import Server  # noqa: E402


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
