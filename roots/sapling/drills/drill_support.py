"""Standard-library First Roots qualification; no other component is imported."""

from __future__ import annotations

import fcntl
import json
import os
import shlex
import stat
import subprocess
import time
import uuid
from collections.abc import Callable, Iterator
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from urllib.parse import quote, unquote, urlsplit

ALLOWANCE = 10  # Owner's shared authorization for SYL-186 through SYL-189.


class DrillError(Exception):
    pass


def require(condition: object, message: str) -> None:
    if not condition:
        raise DrillError(message)


def constant(value: str) -> Any:
    raise ValueError(f"Non-JSON constant: {value}")


def document(source: str | bytes) -> Any:
    return json.loads(source, parse_constant=constant)


def new_json(path: Path, value: Any) -> None:
    """Never overwrite a request, receipt or report from an earlier attempt."""
    path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    content = (json.dumps(value, ensure_ascii=False, allow_nan=False, indent=2)+'\n').encode()
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
    with os.fdopen(fd, 'wb') as stream:
        stream.write(content)
        stream.flush()
        os.fsync(stream.fileno())


@dataclass(frozen=True)
class Places:
    home: Path
    bin: Path
    evidence: Path

    @classmethod
    def owner(cls) -> Places:
        home = Path.home()
        return cls(home, home / '.local/bin', home / '.local/share/arbol-root-evidence/first-roots')

    @property
    def roots(self) -> Path:
        return self.home / 'Library/Application Support/Arbol/roots'

    @property
    def driver(self) -> Path:
        return self.home / 'Library/Application Support/Arbol/drivers/claude'


class Commands:
    def __init__(self, places: Places, *, login: bool = True) -> None:
        self.places, self.login = places, login

    def run(self, program: str, *arguments: str, seconds: float = 30, status: int = 0,
            cwd: Path | None = None) -> Any:
        args = [str(self.places.bin / program), *arguments]
        env = {'HOME':str(self.places.home), 'USER':os.environ.get('USER',''),
               'LOGNAME':os.environ.get('LOGNAME',os.environ.get('USER','')), 'TERM':'xterm-256color'}
        if self.login:
            args = ['/bin/zsh','-l','-i','-c',shlex.join(args)]
        else:
            env['PATH'] = os.defpath
        try:
            result = subprocess.run(args, env=env, cwd=cwd or self.places.home, stdin=subprocess.DEVNULL,
                                    capture_output=True, text=True, timeout=seconds, check=False)
        except subprocess.TimeoutExpired as error:
            raise DrillError(f'{program} exceeded {seconds} seconds; do not automatically repeat a submission.') from error
        except OSError as error:
            raise DrillError(f'{program} could not start.') from error
        if result.returncode != status:
            raise DrillError(f'{program} returned {result.returncode}, expected {status}: {result.stdout[:4096]}')
        try:
            return document(result.stdout)
        except (ValueError, UnicodeError) as error:
            raise DrillError(f'{program} did not return one JSON document.') from error


def wait_for(probe: Callable[[], Any], *, seconds: float, interval: float = 0.1,
             clock: Callable[[], float] = time.monotonic, pause: Callable[[float], None] = time.sleep) -> Any:
    end = clock()+seconds
    while True:
        value = probe()
        if value is not None:
            return value
        remaining = end-clock()
        if remaining <= 0:
            raise DrillError(f'The expected state did not arrive within {seconds} seconds.')
        pause(min(interval,remaining))


class Inspector:
    """Every data inspection runs as one READ ONLY transaction on an explicit Root."""

    def __init__(self, places: Places, *, root: str = 'sapling', psql: str = 'psql',
                 security: str = '/usr/bin/security') -> None:
        require(root.isascii() and root.isalnum() and root.lower() == root, 'Invalid inspection Root identifier.')
        self.places, self.psql = places, psql
        record = document((places.roots / root / 'root.json').read_bytes())
        require(record.get('root') == root and type(record.get('rootContract')) is int
                and record['rootContract'] == 1, 'Unexpected inspection Root/contract.')
        name = record.get('database')
        require(isinstance(name,str) and name and '\0' not in name, 'The Root must name its database.')
        config = document((places.home / '.arbol/database.json').read_bytes())
        address = urlsplit(config['address'])
        require(address.scheme in ('postgresql','postgres') and address.username and address.hostname
                and address.password is None and address.path in ('','/') and not address.query and not address.fragment,
                'Unexpected database address; no password, database or query is permitted.')
        self.address = address._replace(path='/'+quote(name,safe=''),query='connect_timeout=2').geturl()
        self.environment = {'HOME':str(places.home),'PATH':os.environ.get('PATH',os.defpath),'LANG':'en_US.UTF-8'}
        try:
            result = subprocess.run([security,'find-generic-password','-s','com.sylvan-stack.arbol.database',
                                     '-a',unquote(address.username),'-w'], env=self.environment,cwd=places.home,
                                    capture_output=True,text=True,timeout=2,check=False)
        except (OSError,subprocess.TimeoutExpired) as error:
            raise DrillError('The database credential lookup did not answer.') from error
        require(result.returncode in (0,44), 'The database credential lookup failed.')
        if result.returncode == 0:
            self.environment['PGPASSWORD'] = result.stdout.removesuffix('\n')

    def read(self, sql: str, *, seconds: float = 10) -> Any:
        require(sql.strip().upper().startswith('SELECT ') and ';' not in sql,
                'An inspection is exactly one SELECT, inside a READ ONLY transaction.')
        try:
            answer = subprocess.run([self.psql,'--no-psqlrc','--no-password','--quiet','--no-align','--tuples-only',
                                     '--set','ON_ERROR_STOP=1','--dbname',self.address,
                                     '--command','BEGIN READ ONLY; '+sql+'; ROLLBACK;'],
                                    env=self.environment,cwd=self.places.home,stdin=subprocess.DEVNULL,
                                    capture_output=True,text=True,timeout=seconds,check=False)
        except (OSError,subprocess.TimeoutExpired) as error:
            raise DrillError('Read-only database inspection did not answer.') from error
        # Never echo SQL client diagnostics: they may repeat connection/account details.
        require(answer.returncode == 0, 'Read-only database inspection failed.')
        try:
            return document(answer.stdout)
        except ValueError as error:
            raise DrillError('Read-only database inspection did not return one JSON value.') from error

    def counts(self) -> dict[str, int]:
        result = self.read("SELECT json_build_object("+','.join(
            "'"+name+"',(SELECT count(*) FROM "+name+')' for name in
            ['chats','exchanges','messages','tool_calls','runs'])+')')
        require(isinstance(result,dict), 'Table counts were not an object.')
        return dict(result)


class Budget:
    """Append-only attempt history; torn or unknown history refuses new spending."""

    def __init__(self, folder: Path) -> None:
        self.folder = folder

    @contextmanager
    def locked(self) -> Iterator[int]:
        self.folder.mkdir(parents=True,exist_ok=True,mode=0o700)
        lock = os.open(self.folder / 'live-message-budget.lock',os.O_RDWR|os.O_CREAT|os.O_NOFOLLOW,0o600)
        try:
            require(stat.S_ISREG(os.fstat(lock).st_mode), 'The message-budget lock is not regular.')
            try:
                fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
            except BlockingIOError as error:
                raise DrillError('Another message-budget operation is in progress.') from error
            fd = os.open(self.folder / 'live-message-budget.jsonl',os.O_RDWR|os.O_APPEND|os.O_CREAT|os.O_NOFOLLOW,0o600)
            try:
                require(stat.S_ISREG(os.fstat(fd).st_mode), 'The message-budget journal is not regular.')
                yield fd
            finally:
                os.close(fd)
        finally:
            os.close(lock)

    @staticmethod
    def attempts(fd: int) -> dict[str, dict[str, Any]]:
        os.lseek(fd,0,os.SEEK_SET)
        with os.fdopen(os.dup(fd),'rb') as stream:
            data = stream.read()
        require(not data or data.endswith(b'\n'), 'The message-budget journal has an incomplete final event.')
        result: dict[str,dict[str,Any]] = {}
        try:
            for line in data.splitlines():
                event = document(line)
                require(isinstance(event,dict) and type(event.get('version')) is int and event['version'] == 1,
                        'Unknown message-budget event.')
                key = str(uuid.UUID(event['exchange']))
                state = event.get('state')
                require(key == event['exchange'] and state in ('reserved','completed','ambiguous','no_vendor'),
                        'Invalid message-budget identity/state.')
                require((state == 'reserved') != (key in result), 'Invalid message-budget event order.')
                if key in result:
                    require(result[key]['state'] in ('reserved','ambiguous'),
                            'A terminal submission outcome cannot be replaced or refunded.')
                result[key] = event
        except (ValueError,KeyError,TypeError) as error:
            raise DrillError('The message-budget journal is unreadable; reconcile it before submitting.') from error
        return result

    @staticmethod
    def append(fd: int, event: dict[str, Any]) -> None:
        value = (json.dumps(event,allow_nan=False,separators=(',',':'))+'\n').encode()
        require(os.write(fd,value) == len(value), 'The message-budget event was not fully saved.')
        os.fsync(fd)

    def reserve(self, exchange: str, beat: str = 'SYL-186') -> None:
        require(str(uuid.UUID(exchange)) == exchange, 'A submission needs a canonical Exchange UUID.')
        require(beat in ('SYL-186','SYL-187','SYL-188','SYL-189'), 'The shared allowance belongs to First Roots.')
        with self.locked() as fd:
            previous = self.attempts(fd)
            require(exchange not in previous, 'This attempt already exists; inspect it instead of submitting again.')
            used = sum(row['state'] != 'no_vendor' for row in previous.values())
            require(used < ALLOWANCE, 'The ten-message owner allowance is exhausted; no submission was made.')
            self.append(fd,{'version':1,'exchange':exchange,'beat':beat,'state':'reserved','at':time.time()})

    def finish(self, exchange: str, state: str, *, usage: dict[str, Any] | None = None) -> None:
        require(state in ('completed','ambiguous','no_vendor'), 'Invalid submission outcome.')
        with self.locked() as fd:
            previous = self.attempts(fd)
            require(exchange in previous, 'A submission outcome has no prior reservation.')
            require(previous[exchange]['state'] in ('reserved','ambiguous'),
                    'A completed submission cannot be replaced or refunded.')
            self.append(fd,{**previous[exchange],'state':state,'at':time.time(),'usage':usage})

    def status(self) -> dict[str, Any]:
        with self.locked() as fd:
            attempts = self.attempts(fd)
        used = sum(row['state'] != 'no_vendor' for row in attempts.values())
        return {'limit':ALLOWANCE,'usedOrReserved':used,'remaining':ALLOWANCE-used,'attempts':list(attempts.values())}
