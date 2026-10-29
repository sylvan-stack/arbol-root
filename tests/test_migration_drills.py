# Shared fixtures only; test bodies are in top/ and mid/. See TESTS.md.
"""Jensen helpers use disposable PostgreSQL, fictional rows and owned private clients only."""

from __future__ import annotations

import contextlib
import os
import shlex
import sys
import unittest
from pathlib import Path
from types import SimpleNamespace
from typing import Any, cast

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
sys.path.insert(0,str(ROOT/'roots/sapling/drills'))
from drill_support import Inspector, Places  # noqa: E402
from trunk_drill_support import Frame  # noqa: E402

from scripts.migration_fixtures import seed  # noqa: E402
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


class Creation(unittest.TestCase):
    pass  # TEST-TIER-EMPTY-SUITE; helpers remain importable.


class RootOwnership(unittest.TestCase):
    pass  # TEST-TIER-EMPTY-SUITE; helpers remain importable.


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


class ReadyJudgment(unittest.TestCase):
    pass  # TEST-TIER-EMPTY-SUITE; helpers remain importable.


class ReimportJudgment(unittest.TestCase):
    pass  # TEST-TIER-EMPTY-SUITE; helpers remain importable.


# Archived complete imports; restore needed names in their original scope, not at this file tail.
