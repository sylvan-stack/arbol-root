# Shared fixtures only; test bodies are in top/ and mid/. See TESTS.md.
"""First Roots drill helpers use private state and their own PostgreSQL server."""

from __future__ import annotations

import json
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
from drill_support import Commands, DrillError, Inspector, Places  # noqa: E402


class Outage(unittest.TestCase):
    pass  # TEST-TIER-EMPTY-SUITE; helpers remain importable.


class Frame(unittest.TestCase):
    def setUp(self) -> None:
        temporary = tempfile.TemporaryDirectory(prefix="private sapling drill '")
        self.addCleanup(temporary.cleanup)
        self.home = Path(temporary.name).resolve()
        self.places = Places(self.home,self.home/'bin',self.home/'evidence')
        self.places.bin.mkdir()


class ReadOnly(unittest.TestCase):
    pass  # TEST-TIER-EMPTY-SUITE; helpers remain importable.


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
                'runs':[{'outcome':'completed','usage':{'inputTokens':10,'outputTokens':3,'costUsd':0.001}}]}


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


# Archived complete imports; restore needed names in their original scope, not at this file tail.
