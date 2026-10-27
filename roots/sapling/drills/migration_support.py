"""Explicit Root snapshots and owned SQL clients for Jensen operational drills (ARC-D73)."""

from __future__ import annotations

import hashlib
import json
import os
import select
import shlex
import signal
import subprocess
import time
from pathlib import Path
from typing import Any

from drill_support import Inspector, new_json, require, wait_for
from trunk_drill_support import Exchange, Frame, processes

KEYS = {'chats':('id',),'exchanges':('id',),'messages':('exchange_id','position'),
        'tool_calls':('exchange_id','position'),'runs':('exchange_id','run_id'),'migrated_chats':('chat_id',)}
TABLES = tuple(name for name in KEYS if name != 'migrated_chats')


class Snapshot:
    """Keep server-encoded row strings for exact hashes, alongside decoded inspection values."""

    def __init__(self, inspector: Inspector, *, provenance: bool = False) -> None:
        self.inspector = inspector
        self.tables = (*TABLES, *(['migrated_chats'] if provenance else []))

    def read(self) -> dict[str, Any]:
        parts = []
        for table in self.tables:
            order = ','.join('t.'+key for key in KEYS[table])
            parts += ["'"+table+"'", "(SELECT coalesce(json_agg(row_to_json(t)::text ORDER BY "+order+
                      "),'[]') FROM "+table+' t)']
        sql = ("BEGIN ISOLATION LEVEL REPEATABLE READ READ ONLY; SET LOCAL TIME ZONE 'UTC'; "
               "SELECT json_build_object('snapshotAt',transaction_timestamp(),'isolation',"
               "current_setting('transaction_isolation'),'readOnly',current_setting('transaction_read_only'),"
               "'tables',json_build_object("+','.join(parts)+')); ROLLBACK;')
        i = self.inspector
        result = subprocess.run([i.psql,'--no-psqlrc','--no-password','--quiet','--no-align','--tuples-only',
                                 '--set','ON_ERROR_STOP=1','--dbname',i.address,'--command',sql],
                                cwd=i.places.home,env=i.environment,stdin=subprocess.DEVNULL,
                                capture_output=True,text=True,timeout=20,check=False)
        require(result.returncode == 0, 'The repeatable read-only Root snapshot failed.')
        value = json.loads(result.stdout)
        require(value['isolation'] == 'repeatable read' and value['readOnly'] == 'on',
                'The Root snapshot did not use repeatable read/read only.')
        require(set(value['tables']) == set(self.tables), 'The Root snapshot missed a required table.')
        for table,encoded in value['tables'].items():
            require(isinstance(encoded,list) and all(isinstance(x,str) for x in encoded),
                    'The server did not return encoded rows.')
            value['tables'][table] = {'count':len(encoded),'encodedRows':encoded,
                'sha256':hashlib.sha256(json.dumps(encoded,ensure_ascii=False,separators=(',',':')).encode()).hexdigest(),
                'rows':[json.loads(x) for x in encoded]}
        return dict(value)


def fingerprints(value: dict[str, Any]) -> dict[str, Any]:
    return {name:{key:table[key] for key in ['count','sha256']} for name,table in value['tables'].items()}


def direct_psql(parent: int) -> dict[str, Any] | None:
    """Only a live direct child, with the fixed executable's basename and the command's group."""
    result = subprocess.run(['/bin/ps','-axo','pid=,ppid=,comm='],capture_output=True,text=True,
                            stdin=subprocess.DEVNULL,timeout=5,check=True,
                            env={'PATH':'/usr/bin:/bin','LANG':'C','LC_ALL':'C'})
    candidates = []
    for line in result.stdout.splitlines():
        pid,ppid,command = line.strip().split(maxsplit=2)
        if int(ppid) == parent and Path(command).name == 'psql':
            candidates.append(int(pid))
    current = processes()
    found = [current[pid] for pid in candidates if pid in current and current[pid]['group'] == parent]
    require(len(found) <= 1, 'Multiple owned psql children make the migration phase ambiguous.')
    return dict(found[0]) if found else None


def thaw_client(identity: dict[str, Any]) -> None:
    """Resume inside nested outage/freeze guards without closing them out of stack order."""
    require(processes().get(identity['pid']) == identity, 'The frozen owned SQL client changed identity.')
    os.kill(identity['pid'],signal.SIGCONT)


class Command:
    def __init__(self, frame: Frame, arguments: list[str], name: str) -> None:
        self.frame,self.name = frame,name
        self.output = (frame.evidence/(name+'-stdout.json')).open('xb')
        self.errors = (frame.evidence/(name+'-stderr.txt')).open('xb')
        self.began = time.monotonic()
        self.known: dict[int, dict[str, Any]] = {}
        args = [str(frame.places.bin/'arbol-roots'),*arguments]
        try:
            self.process = subprocess.Popen(['/bin/zsh','-l','-i','-c','exec '+shlex.join(args)],
                cwd=frame.work,stdin=subprocess.DEVNULL,stdout=self.output,stderr=self.errors,start_new_session=True,
                env={'HOME':str(frame.places.home),'USER':os.environ.get('USER',''),
                     'LOGNAME':os.environ.get('LOGNAME',''),'TERM':'xterm-256color'})
        except BaseException:
            self.output.close()
            self.errors.close()
            raise

    def psql(self) -> dict[str, Any] | None:
        require(self.process.poll() is None, 'The migration ended before its source-copy phase was observed.')
        child = direct_psql(self.process.pid)
        if child:
            self.known[child['pid']] = child
        return child

    def finish(self, *, status: int = 0, seconds: float = 55) -> dict[str, Any]:
        require(self.process.wait(timeout=seconds) == status, 'The owned migration returned an unexpected status.')
        self.output.flush()
        value = json.loads((self.frame.evidence/(self.name+'-stdout.json')).read_bytes())
        require(isinstance(value,dict), 'The owned migration did not return one JSON object.')
        result = {'elapsedSeconds':time.monotonic()-self.began,'status':status,'reply':value}
        new_json(self.frame.evidence/(self.name+'-result.json'),result)
        return result

    def close(self) -> None:
        if self.process.poll() is None:
            self.process.terminate()
            try:
                self.process.wait(timeout=8)
            except subprocess.TimeoutExpired:
                self.process.kill()
                self.process.wait(timeout=5)
        current = processes()
        for pid,identity in self.known.items():
            if current.get(pid) == identity:
                try:
                    os.kill(pid,signal.SIGCONT)
                    os.kill(pid,signal.SIGTERM)
                except ProcessLookupError:
                    pass
        wait_for(lambda:True if not any(processes().get(pid) == identity for pid,identity in self.known.items())
                 else None,seconds=8,interval=0.2)
        self.output.close()
        self.errors.close()


class SourceLock:
    """No row mutation; keep a client-owned transaction until rollback/connection loss."""

    def __init__(self, inspector: Inspector, evidence: Path) -> None:
        self.inspector = inspector
        self.errors = (evidence/'source-lock-stderr.txt').open('xb')
        self.process = subprocess.Popen([inspector.psql,'--no-psqlrc','--no-password','--quiet','--no-align',
            '--tuples-only','--set','ON_ERROR_STOP=1','--dbname',inspector.address],
            cwd=inspector.places.home,env=inspector.environment,stdin=subprocess.PIPE,stdout=subprocess.PIPE,
            stderr=self.errors,start_new_session=True)
        try:
            self.identity = processes()[self.process.pid]
            assert self.process.stdin is not None and self.process.stdout is not None
            self.process.stdin.write(b'BEGIN;\nLOCK TABLE chats IN ACCESS EXCLUSIVE MODE;\nSELECT pg_backend_pid();\n')
            self.process.stdin.flush()
            require(bool(select.select([self.process.stdout],[],[],8)[0]), 'The owned source lock was not acquired.')
            self.backend = int(self.process.stdout.readline())
            require(self.backend > 0, 'The source lock has no server-side identity.')
            new_json(evidence/'source-lock.json',{'clientPid':self.process.pid,'backendPid':self.backend,
                                               'started':self.identity['started'].isoformat()})
        except BaseException:
            self.close()
            raise

    def blocked_copy(self) -> dict[str, Any] | None:
        require(processes().get(self.process.pid) == self.identity and self.process.poll() is None,
                'The owned source lock process changed.')
        value = self.inspector.read("SELECT coalesce(json_agg(json_build_object('pid',pid,'query',query,"
            "'wait',wait_event_type,'blockers',pg_blocking_pids(pid))),'[]') FROM pg_stat_activity "
            "WHERE datname=current_database() AND wait_event_type='Lock' AND query LIKE 'COPY %chats%TO STDOUT%' "
            'AND '+str(self.backend)+' = ANY(pg_blocking_pids(pid))')
        require(isinstance(value,list) and len(value) <= 1, 'The blocked source COPY is ambiguous.')
        return dict(value[0]) if value else None

    def close(self) -> None:
        if self.process.poll() is None:
            try:
                assert self.process.stdin is not None
                self.process.stdin.write(b'ROLLBACK;\n\\q\n')
                self.process.stdin.flush()
            except (OSError,ValueError):
                pass
            try:
                self.process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.process.terminate()
                try:
                    self.process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    self.process.kill()
                    self.process.wait(timeout=5)
        for stream in [self.process.stdin,self.process.stdout]:
            if stream is not None:
                try:
                    stream.close()
                except OSError:
                    pass
        self.errors.close()


class MigrationFrame(Frame):
    def __init__(self, name: str, *, current: str = 'sapling') -> None:
        self.current = current
        super().__init__(name)

    def preflight(self, *, allow_owned: bool = False) -> None:
        roots = self.calls.run('arbol-roots','list')
        require(any(row.get('root') == self.current and row.get('status') == 'working' and row.get('current')
                    for row in roots), 'The expected current Root changed; inspect the phase receipt.')
        allowed = {x.id for x in self.exchanges} if allow_owned else set()
        for row in roots:
            listing = self.calls.run('arbol-root','--root',row['root'],'list')
            require(not listing.get('unreadable') and all(item['exchange'] in allowed for item in listing['exchanges']),
                    'Unrelated or unreadable Exchange work prevents this migration drill.')
        require(not list((self.places.driver/'runs').iterdir()), 'A normal Claude Driver run prevents this drill.')
        require(self.service.healthy(), 'The database server is not healthy.')

    def root_exchange(self, root: str, scenario: str | None, chat: str | None = None) -> Exchange:
        value = Exchange(self,scenario,chat,root=root)
        self.exchanges.append(value)
        return value

    def close(self) -> None:
        super().close()
        require(not any((self.places.roots/'jensen/exchanges').iterdir()), 'A Jensen Exchange folder remains.')
