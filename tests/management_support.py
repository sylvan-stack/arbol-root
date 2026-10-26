"""Disposable manager context and external launcher, shared by stop/settle tests."""

from __future__ import annotations

import json
import os
import shlex
import shutil
import signal
import subprocess
import sys
import tempfile
import time
import unittest
from pathlib import Path
from typing import Any

from arbol_root.model import Identity
from arbol_root.process import started_at

ROOT = Path(__file__).resolve().parents[1]
INVENTORY: dict[str, Any] = {'root':'sapling', 'rootContract':1, 'trunks':[{'trunk':'trivial', 'builds':[
    {'build':'a', 'status':'working', 'fits':True, 'runnable':True, 'chosen':True}]}]}


class Fixture:
    def __init__(self, case: unittest.TestCase) -> None:
        temporary = tempfile.TemporaryDirectory(prefix='root-management-')
        case.addCleanup(temporary.cleanup)
        self.base = Path(temporary.name).resolve()
        self.root, self.bin = self.base / 'private root', self.base / 'private bin'
        self.root.mkdir()
        self.bin.mkdir()
        (self.root / 'root.json').write_text('{"root":"sapling"}')
        self.exchanges = self.root / 'exchanges'
        self.exchanges.mkdir()
        shutil.copy2(ROOT / 'tests/standin_trunk.py', self.bin / 'standin.py')
        program = self.bin / 'arbol-trunk'
        program.write_text('#!/bin/sh\nexec '+shlex.quote(sys.executable)+' -I -B '+
                           shlex.quote(str(self.bin / 'standin.py'))+' "$@"\n')
        program.chmod(0o755)
        self.context = Identity('sapling', '0', '1.0.0', self.root, self.bin)
        self.case = case
        self.children: list[subprocess.Popen[bytes]] = []
        self.group_children: dict[int, int] = {}
        case.addCleanup(self.end_groups)
        self.script()

    def script(self, **settling: object) -> None:
        (self.bin / 'script.json').write_text(json.dumps({'responses':{
            'list':{'stdout':json.dumps(INVENTORY)+'\n'}, 'settle':{'settled':'interrupted', **settling}}}))

    def put(self, record: dict[str, Any]) -> Path:
        folder = self.exchanges / str(record['exchange'])
        folder.mkdir(exist_ok=True)
        (folder / 'record.json').write_text(json.dumps(record))
        (folder / 'control').write_bytes(b'')
        return folder

    def calls(self) -> list[dict[str, Any]]:
        path = self.bin / 'calls.jsonl'
        return [json.loads(line) for line in path.read_text().splitlines()] if path.exists() else []

    def live(self, value: dict[str, Any], mode: str = 'term') -> tuple[Path, subprocess.Popen[bytes]]:
        folder = self.put(value)
        child = subprocess.Popen([sys.executable, '-I', '-B', str(ROOT / 'tests/exchange_process.py'), str(folder), mode],
                                 start_new_session=True, stdin=subprocess.DEVNULL,
                                 stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        self.children.append(child)
        deadline = time.monotonic()+5
        while not (folder / 'ready').exists():
            self.case.assertIsNone(child.poll())
            self.case.assertLess(time.monotonic(), deadline)
            time.sleep(0.01)
        began = started_at(child.pid)
        assert began is not None
        value['process'] = {'pid':child.pid, 'startedAt':began.isoformat()}
        if (folder / 'child-pid').exists():
            self.group_children[child.pid] = int((folder / 'child-pid').read_text())
        (folder / 'record.json').write_text(json.dumps(value))
        return folder, child

    def end_groups(self) -> None:
        for child in self.children:
            if child.poll() is None:
                try:
                    os.killpg(child.pid, signal.SIGKILL)
                except ProcessLookupError:
                    pass
            member = self.group_children.get(child.pid)
            if member is not None:
                try:
                    if os.getpgid(member) == child.pid:
                        os.kill(member, signal.SIGKILL)
                except ProcessLookupError:
                    pass
            child.wait(timeout=5)

    def cli(self, *args: str) -> subprocess.CompletedProcess[bytes]:
        return subprocess.run([sys.executable, '-I', '-B', str(ROOT / 'bin/entry.py'), '--root', 'sapling',
                               '--root-dir', str(self.root), '--bin-dir', str(self.bin), *args],
                              env={**os.environ, 'HOME':str(self.base)}, capture_output=True, check=False, timeout=15)
