"""Installed First Sapling drills: isolated Driver homes and owned Exchange recovery."""

from __future__ import annotations

import hashlib
import json
import os
import shlex
import shutil
import signal
import subprocess
import sys
import tempfile
import uuid
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from drill_support import Commands, Inspector, Places, document, new_json, require, wait_for
from sapling_messages import snapshot
from sapling_outage import Installed, rows

REPOSITORY = Path(__file__).resolve().parents[3]
STANDIN = REPOSITORY/'contract/conformance/standin/driver.py'


def processes() -> dict[int, dict[str, Any]]:
    """Read start identities and groups without treating a zombie as running."""
    result = subprocess.run(['/bin/ps','-axo','pid=,pgid=,stat=,lstart='],stdin=subprocess.DEVNULL,
                            capture_output=True,text=True,timeout=5,check=True,
                            env={'PATH':'/usr/bin:/bin','LANG':'C','LC_ALL':'C','TZ':'UTC'})
    found = {}
    for line in result.stdout.splitlines():
        if not line.strip():
            continue
        pid,group,state,began = line.split(maxsplit=3)
        if state.startswith(('Z','X')):
            continue
        started = datetime.strptime(' '.join(began.split()),'%a %b %d %H:%M:%S %Y')
        found[int(pid)] = {'pid':int(pid),'group':int(group),'started':started.replace(tzinfo=UTC)}
    return found


def verify_process(record: dict[str, Any], current: dict[int, dict[str, Any]] | None = None) -> dict[str, Any]:
    process = record.get('process',{})
    pid = process.get('pid')
    require(type(pid) is int and pid > 0, 'The owned Exchange has no positive process identifier.')
    selected = (processes() if current is None else current).get(pid)
    require(selected and selected['group'] == pid and pid != os.getpgrp(),
            'The owned Trunk does not lead a separate live group.')
    assert selected is not None
    began = datetime.fromisoformat(process['startedAt'])
    require(began.utcoffset() is not None and abs((selected['started']-began).total_seconds()) <= 2,
            'The owned Trunk process start identity changed; no signal was sent.')
    return dict(selected)


def existing_rows_unchanged(before: dict[str, Any], after: dict[str, Any]) -> bool:
    """Every pre-existing row is kept byte-for-byte, even as new drill rows accumulate."""
    for table, original in before.items():
        values = {json.dumps(row,sort_keys=True,separators=(',',':')) for row in after[table]}
        if not all(json.dumps(row,sort_keys=True,separators=(',',':')) in values for row in original):
            return False
    return True


def ended_identity(data: dict[str, Any], accepted: dict[str, Any], events: list[dict[str, Any]]) -> None:
    row = data['exchange']
    require(row['id'] == accepted['exchange'] and row['chat_id'] == accepted['chat']
            and row['number'] == accepted['number'] and row['trunk'] == accepted['trunk']
            and row['build'] == accepted['build'], 'The persisted end changed the accepted Exchange identity.')
    endings = [line['end'] for line in events if isinstance(line.get('end'),dict)]
    if row['state'] == 'interrupted':
        require(not endings, 'A recovered interrupted Exchange unexpectedly carries an end.')
    elif (row.get('error') or {}).get('code') != 'folder_unwritable':
        require(len(endings) == 1 and endings[0].get('state') == row['state'],
                'The persisted state does not have exactly one matching file end.')


class StandinHome:
    def __init__(self, launcher: Path, scenario: str) -> None:
        self.home = Path(tempfile.mkdtemp(prefix='sapling-standin-')).resolve()
        self.bin = self.home/'bin'
        self.bin.mkdir(mode=0o700)
        (self.home/'standin').mkdir(mode=0o700)
        shutil.copy2(launcher,self.bin/'arbol-trunk')
        shutil.copy2(STANDIN,self.home/'driver.py')
        require((self.bin/'arbol-trunk').read_bytes() == launcher.read_bytes(), 'The copied Trunk launcher differs.')
        python = os.path.realpath(sys.executable)
        command = ['/usr/bin/env','-i','HOME='+str(self.home),'PATH=/usr/bin:/bin','LANG=en_US.UTF-8',
                   'RCT_STANDIN_AS=arbol-claude-driver',python,'-IB',str(self.home/'driver.py')]
        wrapper = self.bin/'arbol-claude-driver'
        wrapper.write_text('#!/bin/sh\nexec '+shlex.join(command)+' "$@"\n')
        wrapper.chmod(0o700)
        self.part(scenario)

    def part(self, scenario: str) -> None:
        (self.home/'standin/scenario').write_text(scenario+'\n')
        for name in ['release','finish']:
            (self.home/'standin'/name).unlink(missing_ok=True)

    def release(self, *, finish: bool = False) -> None:
        (self.home/'standin'/('finish' if finish else 'release')).write_text('\n')

    def records(self) -> list[dict[str, Any]]:
        file = self.home/'standin/received.jsonl'
        return [document(line) for line in file.read_bytes().splitlines()] if file.exists() else []

    def children(self) -> list[int]:
        file = self.home/'standin/children.jsonl'
        return [document(line)['pid'] for line in file.read_bytes().splitlines()] if file.exists() else []

    def close(self) -> None:
        shutil.rmtree(self.home)


class Exchange:
    def __init__(self, frame: Frame, scenario: str | None, chat: str | None = None) -> None:
        self.frame = frame
        self.id = str(uuid.uuid4())
        self.folder = frame.places.roots/'sapling/exchanges'/self.id
        self.fixture = StandinHome(frame.places.bin/'arbol-trunk',scenario) if scenario is not None else None
        self.accepted: dict[str, Any] = {}
        self.chat = chat
        self.known: dict[int, dict[str, Any]] = {}
        self.child_ids: dict[int, dict[str, Any]] = {}
        self.mode: int | None = None
        self.events_file: Any = None
        self.request = frame.evidence/(self.id+'-request.json')

    def arguments(self, message: str, *, hang: bool = False) -> list[str]:
        route = {'driver':'claude','subscription':'standin' if self.fixture else 'anthropic',
                 'model':'standin-model' if self.fixture else 'haiku'}
        new_json(self.request,{'message':message,'route':route,'workingFolder':str(self.frame.work)})
        args = ['--root','sapling','start','trivial','--exchange',self.id,'--request',str(self.request)]
        if self.chat:
            args += ['--chat',self.chat]
        if self.fixture:
            args += ['--bin-dir',str(self.fixture.bin)]
        # The environment switches are passed only to this owned invocation.
        return ['/usr/bin/env','ARBOL_TEST_TIME_SCALE=1',*(['ARBOL_TEST_HANG=1'] if hang else []),
                str(self.frame.places.bin/'arbol-root'),*args]

    def accept(self, answer: dict[str, Any]) -> None:
        require(answer.get('accepted') is True and answer.get('duplicate') is False
                and answer.get('root') == 'sapling' and answer.get('exchange') == self.id
                and answer.get('trunk') == 'trivial', 'The fresh owned Exchange was not accepted.')
        require(self.chat is None or answer.get('chat') == self.chat, 'The resumed Exchange changed chats.')
        self.accepted = answer
        self.chat = answer['chat']
        new_json(self.frame.evidence/(self.id+'-accepted.json'),answer)
        require(self.record().get('exchange') == self.id, 'The accepted folder has a different identity.')
        self.capture_processes()
        self.events_file = (self.folder/'events.jsonl').open('rb')

    def start(self, message: str = 'First Sapling deterministic drill.', *, hang: bool = False) -> Exchange:
        self.accept(self.frame.invoke(self.arguments(message,hang=hang)))
        return self

    def record(self) -> dict[str, Any]:
        value = document((self.folder/'record.json').read_bytes())
        require(value.get('root') == 'sapling' and value.get('exchange') == self.id,
                'The owned record identity changed.')
        return dict(value)

    def events(self) -> list[dict[str, Any]]:
        if self.events_file is None:
            file = self.folder/'events.jsonl'
            raw = file.read_bytes() if file.exists() else b''
        else:
            raw = os.pread(self.events_file.fileno(),os.fstat(self.events_file.fileno()).st_size,0)
        return [document(line) for line in raw.split(b'\n')[:-1] if line]

    def event(self, kind: str, *, seconds: float = 25) -> dict[str, Any]:
        return dict(wait_for(lambda:next((x['event'] for x in self.events()
                                         if x.get('event',{}).get('type') == kind),None),seconds=seconds))

    def capture_processes(self) -> None:
        current = processes()
        leader = verify_process(self.record(),current)
        self.known.update({pid:row for pid,row in current.items() if row['group'] == leader['pid']})
        if self.fixture:
            self.child_ids.update({pid:current[pid] for pid in self.fixture.children() if pid in current})

    def gone(self) -> bool:
        current = processes()
        identities = {**self.known,**self.child_ids}
        return not any(current.get(pid) == identity for pid,identity in identities.items())

    def kill_trunk(self) -> None:
        self.capture_processes()
        leader = verify_process(self.record())
        os.kill(leader['pid'],signal.SIGKILL)

    def persisted(self) -> dict[str, Any]:
        return snapshot(self.frame.inspector,self.id)

    def finish(self, state: str, *, seconds: float = 35) -> dict[str, Any]:
        def ended() -> dict[str, Any] | None:
            data = self.persisted()
            row = data.get('exchange') or {}
            return data if row.get('state') == state and not self.folder.exists() else None
        data = dict(wait_for(ended,seconds=seconds,interval=0.2))
        wait_for(lambda:True if self.gone() else None,seconds=20,interval=0.2)
        ended_identity(data,self.accepted,self.events())
        self.save(data)
        return data

    def save(self, data: dict[str, Any] | None = None) -> None:
        value = {'accepted':self.accepted,'events':self.events(),'persisted':data or self.persisted(),
                 'knownProcesses':[{**row,'started':row['started'].isoformat()}
                                   for row in {**self.known,**self.child_ids}.values()],
                 'standin':self.fixture.records() if self.fixture else None}
        path = self.frame.evidence/(self.id+'-snapshot.json')
        if not path.exists():
            new_json(path,value)

    def listing_state(self) -> str | None:
        listing = self.frame.calls.run('arbol-root','--root','sapling','list')
        return next((row['state'] for row in listing['exchanges'] if row['exchange'] == self.id),None)

    def settle(self, state: str) -> dict[str, Any]:
        result = self.frame.calls.run('arbol-root','--root','sapling','settle',self.id,seconds=35)
        require(result == {'root':'sapling','results':[{'exchange':self.id,'settled':state}]},
                'The owned settle result differs.')
        return self.finish(state)

    def close(self) -> None:
        if self.mode is not None and self.folder.exists():
            self.folder.chmod(self.mode)
        if not self.accepted and self.folder.exists():
            # A timeout can hide an acceptance. Own UUID plus the matching Root record permits cleanup,
            # never a resubmission or a successful verdict.
            record = self.record()
            self.accepted = {'exchange':self.id,'cleanupOfAmbiguousStart':True}
            if record.get('process',{}).get('pid') in processes():
                self.capture_processes()
            if self.events_file is None and (self.folder/'events.jsonl').exists():
                self.events_file = (self.folder/'events.jsonl').open('rb')
        if self.accepted:
            if not self.gone():
                try:
                    self.frame.calls.run('arbol-root','--root','sapling','stop','--force',self.id,seconds=45)
                finally:
                    # A killed leader may leave an orphan Driver. Signal only the captured, still-identical PID.
                    current = processes()
                    for pid,identity in {**self.known,**self.child_ids}.items():
                        if current.get(pid) == identity:
                            try:
                                os.kill(pid,signal.SIGTERM)
                            except ProcessLookupError:
                                pass
                    wait_for(lambda:True if self.gone() else None,seconds=20,interval=0.2)
            if self.folder.exists():
                self.frame.calls.run('arbol-root','--root','sapling','settle',self.id,seconds=35)
            self.save()
        if self.events_file is not None:
            self.events_file.close()
        if self.fixture:
            self.fixture.close()


class Frame:
    def __init__(self, name: str, places: Places | None = None) -> None:
        self.places = places or Places.owner()
        self.calls = Commands(self.places)
        self.inspector = Inspector(self.places)
        self.evidence = self.places.evidence/'trunk-drills'/name/str(uuid.uuid4())
        self.evidence.mkdir(parents=True,mode=0o700)
        self.work = self.evidence/'work'
        self.work.mkdir(mode=0o700)
        self.exchanges: list[Exchange] = []
        self.before = rows(self.inspector)
        self.service = Installed(self.places,self.inspector)
        self.preflight()
        new_json(self.evidence/'before.json',self.before)

    def invoke(self, arguments: list[str], *, seconds: float = 30) -> dict[str, Any]:
        env = {'HOME':str(self.places.home),'USER':os.environ.get('USER',''),
               'LOGNAME':os.environ.get('LOGNAME',os.environ.get('USER','')),'TERM':'xterm-256color'}
        answer = subprocess.run(['/bin/zsh','-l','-i','-c',shlex.join(arguments)],cwd=self.work,env=env,
                                stdin=subprocess.DEVNULL,capture_output=True,text=True,timeout=seconds,check=False)
        require(answer.returncode == 0, 'The owned CLI command refused: '+answer.stdout[:2000])
        value = document(answer.stdout)
        require(isinstance(value,dict), 'The owned CLI did not return one JSON object.')
        return dict(value)

    def preflight(self, *, allow_owned: bool = False) -> None:
        roots = self.calls.run('arbol-roots','list')
        require(any(row.get('root') == 'sapling' and row.get('status') == 'working' and row.get('current')
                    for row in roots), 'First Sapling must be working/current.')
        allowed = {x.id for x in self.exchanges} if allow_owned else set()
        for row in roots:
            listing = self.calls.run('arbol-root','--root',row['root'],'list')
            require(not listing.get('unreadable') and all(item['exchange'] in allowed for item in listing['exchanges']),
                    'Unrelated or unreadable Exchange work prevents this drill.')
        require(not list((self.places.driver/'runs').iterdir()), 'A normal Claude Driver run prevents this drill.')
        require(self.service.healthy(), 'The database server is not healthy.')

    def exchange(self, scenario: str | None, chat: str | None = None) -> Exchange:
        value = Exchange(self,scenario,chat)
        self.exchanges.append(value)
        return value

    def close(self) -> None:
        failures = []
        for exchange in reversed(self.exchanges):
            try:
                exchange.close()
            except BaseException as error:
                failures.append(str(error))
        after = rows(self.inspector)
        new_json(self.evidence/'after.json',after)
        require(existing_rows_unchanged(self.before,after), 'A pre-existing Root row changed during the drill.')
        require(not failures, 'Owned drill cleanup failed: '+str(failures))
        self.preflight()
        require(not any((self.places.roots/'sapling/exchanges').iterdir()), 'An Exchange folder remains after cleanup.')

    def proof(self) -> dict[str, Any]:
        return {'passed':True,'evidence':str(self.evidence),'exchanges':[x.id for x in self.exchanges],
                'preExistingRowsUnchanged':True,'serviceRestored':self.service.healthy(),
                'timeScale':1,
                'standinSourceSHA256':hashlib.sha256(STANDIN.read_bytes()).hexdigest()}


def interrupted_rows(data: dict[str, Any], *, tool: bool = True) -> None:
    require(data['exchange']['state'] == 'interrupted' and data['runs']
            and all(row['outcome'] == 'interrupted' for row in data['runs']), 'The recovered run did not become interrupted.')
    require(any(row['role'] == 'assistant' and row['text'] == 'Recover this text.' for row in data['messages']),
            'The arrived text was lost during settling.')
    if tool:
        # snapshot intentionally carries only messages/runs; read the tool row with the caller's Inspector.
        require(any(x.get('usage',{}).get('inputTokens') == 41 for x in data['runs']),
                'The arrived usage was lost during settling.')
