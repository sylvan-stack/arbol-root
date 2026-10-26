"""One verified append-only stop request, then record observation and bounded escalation."""

from __future__ import annotations

import json
import os
import stat
import subprocess
import time
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from arbol_root.clock import awake
from arbol_root.launcher import Reply
from arbol_root.listing import project, read_record
from arbol_root.model import Identity, Refusal
from arbol_root.settle import settle_after_stop

ENDS = {'completed', 'failed', 'cancelled', 'interrupted'}


@dataclass(frozen=True)
class Observed:
    process: dict[str, Any]
    alive: bool
    end: str | None


def read_exchange(context: Identity, exchange: str) -> Observed | None:
    place = context.folder / 'exchanges'
    try:
        catalogue = os.open(place, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
    except FileNotFoundError:
        return None
    except OSError as error:
        raise Refusal('root_unavailable', f'Cannot read {place}: {error}') from error
    try:
        try:
            record = read_record(catalogue, exchange)
            os.stat(exchange, dir_fd=catalogue, follow_symlinks=False)
            view = project(record, context, exchange)
            return Observed(record['process'], view['process']['alive'], record.get('end', {}).get('state'))
        except (OSError, ValueError, KeyError, TypeError, subprocess.SubprocessError) as error:
            try:
                os.stat(exchange, dir_fd=catalogue, follow_symlinks=False)
            except FileNotFoundError:
                return None
            raise Refusal('root_unavailable', f'Cannot verify Exchange {exchange}: {error}') from error
    finally:
        os.close(catalogue)


def pending(context: Identity, exchange: str) -> bool:
    place = context.folder / 'exchanges' / ('.'+exchange+'.new')
    try:
        metadata = place.lstat()
        if not stat.S_ISDIR(metadata.st_mode):
            raise ValueError('The publishing name is not a real directory.')
        return True
    except FileNotFoundError:
        return False
    except (OSError, ValueError) as error:
        raise Refusal('root_unavailable', f'Cannot verify {place}: {error}') from error


def same_process(observed: Observed, expected: Observed) -> None:
    if any(observed.process[key] != expected.process[key] for key in ['pid', 'startedAt']):
        raise Refusal('root_unavailable', 'The recorded process changed while stop was running.')


def append_stop(context: Identity, exchange: str, expected: Observed) -> None:
    catalogue = directory = descriptor = None
    try:
        catalogue = os.open(context.folder / 'exchanges', os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
        directory = os.open(exchange, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=catalogue)
        record = read_record(directory, '.')
        view = project(record, context, exchange)
        same_process(Observed(record['process'], view['process']['alive'], record.get('end', {}).get('state')), expected)
        if not view['process']['alive'] or 'end' in record:
            return
        descriptor = os.open('control', os.O_WRONLY | os.O_APPEND | os.O_NONBLOCK | os.O_NOFOLLOW, dir_fd=directory)
        if not stat.S_ISREG(os.fstat(descriptor).st_mode):
            raise ValueError('control is not a regular file.')
        named = os.stat(exchange, dir_fd=catalogue, follow_symlinks=False)
        opened = os.fstat(directory)
        if (named.st_dev, named.st_ino) != (opened.st_dev, opened.st_ino):
            raise ValueError('The Exchange folder changed before its control write.')
        line = b'{"type":"stop"}\n'
        if os.write(descriptor, line) != len(line):
            raise ValueError('The stop line could not be written completely; it was not retried.')
    except FileNotFoundError as error:
        if read_exchange(context, exchange) is not None:
            raise Refusal('root_unavailable', f'Cannot append to existing control: {error}') from error
    except (OSError, ValueError, KeyError, TypeError, subprocess.SubprocessError) as error:
        raise Refusal('root_unavailable', f'Cannot append a stop line: {error}') from error
    finally:
        for fd in [descriptor, directory, catalogue]:
            if fd is not None:
                os.close(fd)


def force_end(context: Identity, exchange: str, expected: Observed,
              clock: Callable[[], float], pause: Callable[[float], None]) -> bool:
    raise Refusal('not_ended', 'Forced group termination is not available in this unmerged candidate.')


def result(context: Identity, exchange: str, ended: str, forced: bool,
           settling: dict[str, Any] | None = None) -> Reply:
    document: dict[str, Any] = {'root':context.root, 'exchange':exchange, 'ended':ended, 'forced':forced}
    if settling is not None:
        document['settling'] = settling
    return Reply((json.dumps(document, ensure_ascii=True)+'\n').encode(), document, 0)


def save_ended(context: Identity, exchange: str, observed: Observed, forced: bool) -> Reply:
    saved = settle_after_stop(context, exchange)
    state = saved.get('settled')
    ended = 'saved' if state == 'none' else state if isinstance(state, str) and state in ENDS else observed.end or 'interrupted'
    return result(context, exchange, ended, forced, saved)


def stop(context: Identity, exchange: str, force: bool = False, *,
         clock: Callable[[], float] = awake, pause: Callable[[float], None] = time.sleep) -> Reply:
    observed = read_exchange(context, exchange)
    deadline = clock()+15
    while observed is None and pending(context, exchange) and clock() < deadline:
        pause(min(0.1, max(0, deadline-clock())))
        observed = read_exchange(context, exchange)
    if observed is None:
        return result(context, exchange, 'none', False)
    if not observed.alive:
        return save_ended(context, exchange, observed, False)
    if observed.end is not None:
        return result(context, exchange, observed.end, False)
    expected = observed
    if not force:
        append_stop(context, exchange, expected)
        deadline = clock()+20
        while True:
            observed = read_exchange(context, exchange)
            if observed is None:
                return result(context, exchange, 'saved', False)
            same_process(observed, expected)
            if not observed.alive:
                return save_ended(context, exchange, observed, False)
            if observed.end is not None:
                return result(context, exchange, observed.end, False)
            if clock() >= deadline:
                break
            pause(min(0.1, max(0, deadline-clock())))
    forced = force_end(context, exchange, expected, clock, pause)
    observed = read_exchange(context, exchange) or expected
    return save_ended(context, exchange, observed, forced)
