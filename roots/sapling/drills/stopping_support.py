"""Verified single-process freezing and owned manager commands for installed drills."""

from __future__ import annotations

import os
import shlex
import signal
import subprocess
import sys
import time
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path
from types import FrameType
from typing import Any

from drill_support import document, new_json, require, wait_for
from trunk_drill_support import REPOSITORY, Exchange, Frame, processes, verify_process


@contextmanager
def frozen(identity: dict[str, Any], receipt: Path) -> Iterator[None]:
    """Always thaw the anchored surviving PID, including through a catchable interrupt."""
    pid = identity['pid']
    require(type(pid) is int and pid > 0 and pid != os.getpid(), 'A freeze needs an owned positive child PID.')
    require(processes().get(pid) == identity, 'The freeze target no longer has its owned start identity.')
    previous = {n:signal.getsignal(n) for n in (signal.SIGINT,signal.SIGTERM)}
    result: dict[str, Any] = {'pid':pid,'started':identity['started'].isoformat(),'frozen':False,'thawed':False}

    def interrupted(number: int, frame: FrameType | None) -> None:
        raise KeyboardInterrupt('Frozen-process drill interrupted by signal '+str(number))

    try:
        for number in previous:
            signal.signal(number,interrupted)
        try:
            result['frozen'] = True
            os.kill(pid,signal.SIGSTOP)
            yield
        except BaseException as error:
            result['bodyError'] = type(error).__name__
            raise
        finally:
            for number in previous:
                signal.signal(number,signal.SIG_IGN)
            actual = processes().get(pid)
            if result['frozen'] and actual == identity:
                try:
                    os.kill(pid,signal.SIGCONT)
                    result['thawed'] = True
                except ProcessLookupError:
                    result['gone'] = True
            else:
                result['gone'] = True
                result['pidReused'] = actual is not None
            new_json(receipt,result)
    finally:
        for number,handler in previous.items():
            signal.signal(number,handler)


class Manager:
    """One direct child; ending it never signals a Trunk or a different command."""

    def __init__(self, frame: Frame, arguments: list[str], name: str) -> None:
        self.frame = frame
        self.name = name
        self.arguments = arguments
        self.output = (frame.evidence/(name+'-stdout.json')).open('xb')
        self.errors = (frame.evidence/(name+'-stderr.txt')).open('xb')
        self.began = time.monotonic()
        args = [str(frame.places.bin/'arbol-root'),'--root','sapling',*arguments]
        try:
            self.process = subprocess.Popen(['/bin/zsh','-l','-i','-c','exec '+shlex.join(args)],
                cwd=frame.work,stdin=subprocess.DEVNULL,stdout=self.output,stderr=self.errors,start_new_session=True,
                env={'HOME':str(frame.places.home),'USER':os.environ.get('USER',''),
                     'LOGNAME':os.environ.get('LOGNAME',''),'TERM':'xterm-256color'})
        except BaseException:
            self.output.close()
            self.errors.close()
            raise

    def finish(self, *, seconds: float = 45) -> dict[str, Any]:
        require(self.process.wait(timeout=seconds) == 0, 'The owned manager command refused; inspect its output.')
        self.output.flush()
        value = document((self.frame.evidence/(self.name+'-stdout.json')).read_bytes())
        require(isinstance(value,dict), 'The manager reply is not one JSON object.')
        if self.arguments[:1] == ['stop']:
            require(value.get('root') == 'sapling' and value.get('exchange') == self.arguments[-1],
                    'The manager stop reply changed the owned Root/Exchange identity.')
        result = {'elapsedSeconds':time.monotonic()-self.began,'reply':value}
        new_json(self.frame.evidence/(self.name+'-result.json'),result)
        return result

    def kill(self) -> None:
        require(self.process.poll() is None, 'The owned manager already ended before its planned kill.')
        self.process.kill()
        self.process.wait(timeout=5)
        new_json(self.frame.evidence/(self.name+'-killed.json'),
                 {'pid':self.process.pid,'returncode':self.process.returncode,'elapsedSeconds':time.monotonic()-self.began})

    def close(self) -> None:
        if self.process.poll() is None:
            self.process.terminate()
            try:
                self.process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.process.kill()
                self.process.wait(timeout=5)
        self.output.close()
        self.errors.close()


def freeze_exchange(exchange: Exchange, receipt: str) -> Any:
    exchange.capture_processes()
    return frozen(verify_process(exchange.record()),exchange.frame.evidence/receipt)


def ignored_child(exchange: Exchange) -> None:
    """Wrap only this private stand-in launcher; its extra child stays in the Trunk's group."""
    fixture = exchange.fixture
    require(fixture is not None, 'An ignored child belongs only to a private stand-in, never a real Driver.')
    assert fixture is not None
    original = fixture.bin/'arbol-claude-driver'
    base = fixture.bin/'arbol-claude-driver.base'
    original.rename(base)
    source = REPOSITORY/'roots/sapling/drills'
    args = ['/usr/bin/env','-i','HOME='+str(fixture.home),'PATH=/usr/bin:/bin','LANG=en_US.UTF-8',
            os.path.realpath(sys.executable),'-IB',str(source/'stopping_wrapper.py'),str(fixture.home),
            str(base),str(source/'stopping_child.py')]
    original.write_text('#!/bin/sh\nexec '+shlex.join(args)+' "$@"\n')
    original.chmod(0o700)


def wait_ignored_child(exchange: Exchange) -> dict[str, Any]:
    assert exchange.fixture is not None
    file = exchange.fixture.home/'standin/ignored-child.json'
    value = wait_for(lambda:document(file.read_bytes()) if file.exists() else None,seconds=15)
    exchange.capture_processes()
    selected = processes().get(value['pid'])
    require(selected and selected['group'] == exchange.record()['process']['pid'],
            'The private ignored child did not stay in the Trunk group.')
    return dict(value)


def wait_stop(exchange: Exchange) -> None:
    file = exchange.folder/'control'
    wait_for(lambda:True if any(document(line).get('type') == 'stop'
                               for line in file.read_bytes().splitlines()) else None,seconds=10)


def stop_state(result: dict[str, Any], state: str, *, forced: bool) -> None:
    reply = result['reply']
    require(reply.get('ended') in (state,'saved') and reply.get('forced') is forced,
            'The stop reply did not report the expected end and force choice.')
    if forced:
        require(isinstance(reply.get('settling'),dict) and reply['settling'].get('settled') in (state,'none'),
                'The forced stop did not include its settling result.')
