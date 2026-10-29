# Shared fixtures; case bodies live in top/ and mid/. See TESTS.md.
from __future__ import annotations


import json
import os
import shlex
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from typing import Any, cast
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))

from program_support import development  # noqa: E402

from arbol_root.input import parse  # noqa: E402
from arbol_root.model import Identity, Refusal  # noqa: E402
from arbol_root.start import start  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
EXCHANGE = '7f3a2c1e-4b5d-4e6f-8a9b-0c1d2e3f4a5b'
ACCEPTED = '  { "accepted":true, "root":"sapling", "exchange":"'+EXCHANGE+'", "extra":3 }\n'
INVENTORY = {'root':'sapling','rootContract':1,'trunks':[{'trunk':'trivial','builds':[
    {'build':'a','status':'working','fits':True,'runnable':True,'chosen':True}]}]}
POPEN = subprocess.Popen


class Starting(unittest.TestCase):
    def setUp(self) -> None:
        temp = tempfile.TemporaryDirectory(prefix='rtm-start-')
        self.addCleanup(temp.cleanup)
        self.base = Path(temp.name).resolve()
        self.development = development(self.base)
        self.bin = self.base / 'launchers with spaces'
        self.bin.mkdir()
        shutil.copy2(ROOT / 'tests/standin_trunk.py', self.bin / 'standin.py')
        program = self.bin / 'arbol-trunk'
        program.write_text('#!/bin/sh\nexec '+shlex.quote(sys.executable)+' -I -B '+
                           shlex.quote(str(self.bin / 'standin.py'))+' "$@"\n')
        program.chmod(0o755)
        self.root = self.base / 'root'
        self.root.mkdir()
        (self.root / 'root.json').write_text('{"root":"sapling"}')
        self.request = self.base / 'request with spaces'
        self.request.write_bytes(b'\xff the manager never opens this file')
        self.options = ['--exchange',EXCHANGE,'--request',str(self.request)]
        self.context = Identity('sapling','0','1.0.0',self.root,self.bin)
        self.children: list[subprocess.Popen[bytes]] = []
        self.addCleanup(self.clean_children)
        self.script()

    def clean_children(self) -> None:
        for child in self.children:
            if child.poll() is None:
                child.terminate()
            child.wait(timeout=5)

    def spawn(self, *args: Any, **kwargs: Any) -> subprocess.Popen[bytes]:
        child = cast(subprocess.Popen[bytes], POPEN(*args, **kwargs))
        self.children.append(child)
        return child

    def script(self, **run: object) -> None:
        (self.bin / 'script.json').write_text(json.dumps({'responses':{
            'list':{'stdout':json.dumps(INVENTORY)+'\n'}, 'run':{'stdout':ACCEPTED, **run}}}))

    def calls(self) -> list[dict[str, Any]]:
        return [json.loads(line) for line in (self.bin / 'calls.jsonl').read_text().splitlines()]

    def cli(self, extra: list[str] | None = None) -> subprocess.CompletedProcess[bytes]:
        return subprocess.run([sys.executable,'-I','-B',str(self.development / 'bin/entry.py'),'--root','sapling',
                               '--root-dir',str(self.root),'--bin-dir',str(self.bin),'start',*self.options,*(extra or [])],
                              env={**os.environ,'HOME':str(self.base)}, cwd=self.base,
                              capture_output=True, check=False, timeout=10)
