"""Named installed Trunk failure drills, with no vendor call in the aggregate run."""

from __future__ import annotations

import argparse
import fcntl
import json
import os
import pty
import select
import shlex
import signal
import subprocess
import termios
import time
from collections.abc import Callable
from types import FrameType
from typing import Any

from drill_support import Budget, Commands, Places, new_json, require, wait_for
from sapling_messages import usage_available
from sapling_outage import stopped
from trunk_drill_support import Exchange, Frame, interrupted_rows


def tool_rows(exchange: Exchange) -> list[dict[str, Any]]:
    value = exchange.frame.inspector.read("SELECT coalesce(json_agg(t ORDER BY position),'[]') FROM tool_calls t "
                                         "WHERE exchange_id='"+exchange.id+"'")
    require(isinstance(value,list), 'The tool-call inspection did not return rows.')
    return list(value)


def resume(frame: Frame, exchange: Exchange) -> dict[str, Any]:
    following = frame.exchange('R5',exchange.chat).start('Continue after the drill.')
    data = following.finish('completed')
    require(data['exchange']['number'] == exchange.accepted['number']+1,
            'The recovered chat did not accept its next Exchange.')
    return data


def judge_real_interrupted(data: dict[str, Any], events: list[dict[str, Any]]) -> None:
    """RCT-3 preserves whole top-level blocks; a text_delta deliberately makes no row."""
    expected = [(line['n'],line['event']['text']) for line in events
                if line.get('event',{}).get('type') == 'text' and not line['event'].get('parentCallId')]
    actual = [(row['position'],row['text']) for row in data['messages'] if row['role'] == 'assistant']
    require(actual == expected, 'The interrupted real answer differs from the whole blocks RCT-3 keeps.')
    require(data['exchange']['state'] == 'interrupted' and data['runs']
            and all(row['outcome'] == 'interrupted' for row in data['runs']),
            'The real run was not recovered interrupted.')


def killed(frame: Frame, *, real: bool = False) -> dict[str, Any]:
    exchange = frame.exchange(None if real else 'R13 interrupted')
    budget = Budget(frame.places.evidence)
    if real:
        require(frame.calls.run('arbol-claude-driver','subscriptions','check','anthropic').get('state') == 'signed_in',
                'The normal owner Subscription is not signed in.')
        require(usage_available(frame.calls.run('arbol-claude-driver','subscriptions','usage','anthropic'),time.time()),
                'The normal Subscription reports an active or unproved usage limit.')
        history = budget.status()
        require(all((row.get('usage') or {}).get('retryNotBeforeUnix',0) <= time.time()
                    for row in history['attempts']), 'The recorded vendor retry deadline has not passed.')
        budget.reserve(exchange.id,'SYL-187')
    submitted = False
    try:
        submitted = True
        exchange.start('Write 500 numbered sentences about imaginary trees. Begin immediately and do not use tools.'
                       if real else 'Keep this unfinished answer and tool call.')
        exchange.event('text_delta' if real else 'usage',seconds=90 if real else 25)
        arrived = exchange.events()
        exchange.kill_trunk()
        wait_for(lambda:True if exchange.gone() else None,seconds=25,interval=0.2)
        require(exchange.listing_state() == 'interrupted', 'The killed Trunk was not listed interrupted.')
        require('end' not in exchange.record(), 'Killing the Trunk forged an end.')
        data = exchange.settle('interrupted')
        if real:
            judge_real_interrupted(data,arrived)
        else:
            interrupted_rows(data)
            calls = tool_rows(exchange)
            require(len(calls) == 1 and calls[0]['interrupted'] is True and calls[0]['ok'] is False,
                    'The open tool call was not recovered interrupted.')
        resumed = resume(frame,exchange)
        usage = [x['event']['usage'] for x in arrived if x.get('event',{}).get('type') in ('usage','finished')
                 and isinstance(x['event'].get('usage'),dict)]
        report: dict[str, Any] = {'killedExchange':exchange.id,'resumedExchange':resumed['exchange']['id'],
                                  'realMessage':real,'observedUsage':usage,
                                  'reportedCostUSD':usage[-1].get('costUsd') if usage else None}
        if real:
            wait_for(lambda:True if not list((frame.places.driver/'runs').iterdir()) else None,seconds=30,interval=0.2)
            budget.finish(exchange.id,'completed',usage={'outcome':'interrupted','observed':usage,
                                                       'reportedCostUSD':report['reportedCostUSD']})
            report['budget'] = budget.status()
        return report
    except BaseException:
        if real:
            budget.finish(exchange.id,'ambiguous' if submitted else 'no_vendor')
        raise


def hangs(frame: Frame) -> dict[str, Any]:
    exchange = frame.exchange('R7').start(hang=True)
    exchange.event('started')
    fixture = exchange.fixture
    assert fixture is not None
    wait_for(lambda:fixture.children() or None,seconds=15)
    exchange.capture_processes()
    before = exchange.record()
    heartbeat = before['signsOfLife']['heartbeat']
    began = time.monotonic()
    wait_for(lambda:True if exchange.gone() else None,seconds=75,interval=0.25)
    elapsed = time.monotonic()-began
    after = exchange.record()
    require(55 <= elapsed <= 72, 'The real-scale stuck-watch deadline differs from sixty seconds.')
    require(after['signsOfLife']['heartbeat'] == heartbeat and 'end' not in after,
            'The hung work raised its heartbeat or forged an end.')
    require(exchange.listing_state() == 'interrupted', 'The self-ended hung Trunk was not interrupted.')
    data = exchange.settle('interrupted')
    require(data['runs'] and all(row['outcome'] == 'interrupted' for row in data['runs']),
            'The hung run was not recovered interrupted.')
    return {'hungExchange':exchange.id,'elapsedSeconds':elapsed,'standinChildrenGone':exchange.gone(),
            'realMessage':False}


def starter_gone(frame: Frame) -> dict[str, Any]:
    exchange = frame.exchange('R2')
    args = exchange.arguments('Keep working after this terminal disappears.')
    master,slave = pty.openpty()

    def terminal() -> None:
        os.setsid()
        fcntl.ioctl(0,termios.TIOCSCTTY,0)

    process = subprocess.Popen(['/bin/zsh','-l','-i','-c',shlex.join(args)],stdin=slave,stdout=slave,
                               stderr=subprocess.DEVNULL,preexec_fn=terminal,cwd=frame.work,
                               env={'HOME':str(frame.places.home),'USER':os.environ.get('USER',''),
                                    'LOGNAME':os.environ.get('LOGNAME',''),'TERM':'xterm-256color'})
    os.close(slave)
    captured = bytearray()
    try:
        deadline = time.monotonic()+25
        while b'\n' not in captured:
            remaining = deadline-time.monotonic()
            require(remaining > 0, 'The owned terminal starter gave no acceptance line.')
            ready,_,_ = select.select([master],[],[],remaining)
            require(ready, 'The owned terminal starter exceeded its deadline.')
            captured.extend(os.read(master,65536))
        exchange.accept(json.loads(bytes(captured).splitlines()[0]))
        if process.poll() is None:
            process.kill()
        process.wait(timeout=5)
    finally:
        os.close(master)
        if process.poll() is None:
            process.kill()
            process.wait(timeout=5)
    require(exchange.listing_state() == 'running', 'The detached Exchange died with its terminal starter.')
    assert exchange.fixture is not None
    exchange.fixture.release()
    exchange.finish('completed')
    return {'exchange':exchange.id,'starterGone':True,'terminalClosed':True,'realMessage':False}


def judge_database_rows(exchange: Exchange) -> dict[str, Any]:
    data = exchange.persisted()
    texts = [row['text'] for row in data['messages'] if row['role'] == 'assistant']
    require(texts == ['Before the database went away.','Written while the database was away.'],
            'The outage lost or reordered a whole answer block.')
    calls = tool_rows(exchange)
    require(len(calls) == 1 and calls[0]['name'] == 'shell'
            and calls[0]['result'] == {'output':'#!/bin/sh\nset -e\n','exitCode':0},
            'The outage lost or changed the completed tool call.')
    require(len(data['runs']) == 1 and data['runs'][0]['outcome'] == 'completed'
            and data['runs'][0]['usage'] == {'model':'standin-model','inputTokens':31,'outputTokens':9},
            'The outage lost the completed run or its exact usage.')
    return data


def database_mid_run(frame: Frame) -> dict[str, Any]:
    exchange = frame.exchange('R12 middle').start()
    exchange.event('text')
    wait_for(lambda:True if len(exchange.persisted()['messages']) >= 2 else None,seconds=20)
    frame.preflight(allow_owned=True)
    assert exchange.fixture is not None
    with stopped(stop=frame.service.stop,restore=frame.service.restore,healthy=frame.service.healthy,
                 receipt=frame.evidence/'restoration.json'):
        before = exchange.record()['signsOfLife']['heartbeat']
        count = len(exchange.events())
        began = time.monotonic()
        exchange.fixture.release()
        exchange.event('usage')
        wait_for(lambda:True if time.monotonic()-began > 6 and
                 exchange.record()['signsOfLife']['heartbeat'] > before else None,seconds=20,interval=0.2)
        require(len(exchange.events()) > count and not exchange.gone(), 'The offline answer stopped progressing.')
        elapsed = time.monotonic()-began
    wait_for(lambda:True if len(exchange.persisted()['messages']) == 3 and tool_rows(exchange) else None,seconds=20)
    exchange.fixture.release(finish=True)
    exchange.finish('completed')
    judge_database_rows(exchange)
    return {'exchange':exchange.id,'offlineSeconds':elapsed,'outputContinued':True,'heartbeatRose':True,
            'realMessage':False}


def database_through_end(frame: Frame) -> dict[str, Any]:
    exchange = frame.exchange('R12 end').start()
    exchange.event('text')
    frame.preflight(allow_owned=True)
    assert exchange.fixture is not None
    with stopped(stop=frame.service.stop,restore=frame.service.restore,healthy=frame.service.healthy,
                 receipt=frame.evidence/'restoration.json'):
        offline_began = time.monotonic()
        exchange.fixture.release()
        end = wait_for(lambda:exchange.record().get('end'),seconds=20)
        began = time.monotonic()
        wait_for(lambda:True if exchange.gone() else None,seconds=75,interval=0.2)
        elapsed = time.monotonic()-began
        require(55 <= elapsed <= 73, 'The real final-save retry budget differs from sixty seconds.')
        require(end['state'] == 'completed' and exchange.events()[-1].get('end') == end,
                'The offline end was not recoverable in both record and events.')
        require(exchange.listing_state() == 'unsaved', 'The completed offline result was not listed unsaved.')
        new_json(frame.evidence/'offline-record.json',exchange.record())
        wait_for(lambda:True if time.monotonic()-offline_began >= 61 else None,seconds=65,interval=0.2)
        offline = time.monotonic()-offline_began
    data = exchange.settle('completed')
    require(data['exchange']['error'] is None, 'The completed offline result acquired an error.')
    judge_database_rows(exchange)
    return {'exchange':exchange.id,'finalRetrySeconds':elapsed,'offlineSeconds':offline,
            'unsavedBeforeRecovery':True,'realMessage':False}


def folder_unwritable(frame: Frame) -> dict[str, Any]:
    exchange = frame.exchange('R11 folder').start()
    exchange.event('tool_started')
    fixture = exchange.fixture
    assert fixture is not None
    wait_for(lambda:fixture.children() or None,seconds=15)
    exchange.capture_processes()
    exchange.mode = exchange.folder.stat().st_mode & 0o777
    exchange.folder.chmod(0o500)
    try:
        wait_for(lambda:True if exchange.gone() else None,seconds=30,interval=0.2)
        data = exchange.persisted()
        require(data['exchange']['state'] == 'failed' and
                data['exchange']['error']['code'] == 'folder_unwritable' and exchange.folder.is_dir(),
                'The unwritable folder did not leave the specified persisted failure/recovery folder.')
        calls = tool_rows(exchange)
        require(len(calls) == 1 and calls[0]['interrupted'] is True and calls[0]['ok'] is False,
                'The unwritable-folder tool call was not saved interrupted.')
        require(data['runs'][0]['outcome'] == 'cancelled', 'The unwritable-folder run was not stopped.')
    finally:
        if exchange.folder.exists():
            exchange.folder.chmod(exchange.mode)
    recovered = exchange.settle('failed')
    require(recovered == data, 'Settling the unwritable folder changed its saved rows.')
    return {'exchange':exchange.id,'restoredMode':exchange.mode,'realMessage':False}


def failed_or_cancelled(frame: Frame, state: str) -> dict[str, Any]:
    first = frame.exchange('R2 failed' if state == 'failed' else 'R8 tool').start()
    first.event('started')
    other = frame.exchange('R2').start('Another chat must survive this failure.')
    other.event('started')
    require(other.chat != first.chat and other.listing_state() == 'running', 'The parallel chat never started.')
    assert first.fixture is not None and other.fixture is not None
    if state == 'failed':
        first.fixture.release()
    else:
        result = frame.calls.run('arbol-root','--root','sapling','stop',first.id,seconds=30)
        require(result.get('ended') == 'cancelled' and result.get('forced') is False,
                'The requested cancellation was not confirmed gracefully.')
    data = first.finish(state)
    if state == 'failed':
        raw = next(json.loads(line)['error'] for record in first.fixture.records()
                   if record.get('request') for line in record['events']
                   if json.loads(line).get('type') == 'finished')
        require(data['exchange']['error'] == raw, 'The failed Exchange lost part of the Driver error.')
    require(other.listing_state() == 'running' and not other.gone(), 'The other chat ended with the first.')
    resumed = resume(frame,first)
    require(other.listing_state() == 'running', 'Resuming one chat stopped the other.')
    other.fixture.release()
    other.finish('completed')
    return {'exchange':first.id,'otherChat':other.chat,'resumedExchange':resumed['exchange']['id'],
            'state':state,'realMessage':False}


DRILLS: dict[str, Callable[[Frame], dict[str, Any]]] = {
    'trunk-killed':killed,'trunk-hangs':hangs,'starter-gone':starter_gone,
    'database-away-mid-run':database_mid_run,'database-away-through-end':database_through_end,
    'folder-unwritable':folder_unwritable,
    'failed-exchange':lambda frame:failed_or_cancelled(frame,'failed'),
    'cancelled-exchange':lambda frame:failed_or_cancelled(frame,'cancelled')}


def run_drill(name: str, *, real: bool = False) -> dict[str, Any]:
    require(name in DRILLS and (not real or name == 'trunk-killed'), 'Unknown drill or unauthorized real variant.')
    frame = Frame(name+('-real' if real else ''))
    details: dict[str, Any] = {}
    try:
        try:
            details = killed(frame,real=True) if real else DRILLS[name](frame)
        except BaseException as error:
            new_json(frame.evidence/'failure.json',{'error':str(error),'kind':type(error).__name__})
            raise
    finally:
        frame.close()
    report = {'check':'sapling.'+name,**frame.proof(),**details}
    new_json(frame.evidence/'qualified.json',report)
    return report


def entry(name: str) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--run',action='store_true')
    if name == 'trunk-killed':
        parser.add_argument('--real',action='store_true')
    args = parser.parse_args()
    previous = {n:signal.getsignal(n) for n in (signal.SIGINT,signal.SIGTERM)}

    def interrupt(number: int, frame: FrameType | None) -> None:
        raise KeyboardInterrupt('Drill interrupted by signal '+str(number))

    try:
        for number in previous:
            signal.signal(number,interrupt)
        if not args.run:
            p = Places.owner()
            view = Commands(p).run('arbol-root','--root','sapling','list')
            print(json.dumps({'preflightOnly':True,'root':view['root'],'openExchanges':len(view['exchanges']),
                              'drill':name,'remainingSubmissions':Budget(p.evidence).status()['remaining']}))
        elif name == 'all':
            reports = []
            for selected in DRILLS:
                report = run_drill(selected)
                reports.append(report)
                print(json.dumps(report),flush=True)
            print(json.dumps({'check':'sapling.trunk-drills','passed':True,'drills':len(reports),'realMessages':0}))
        else:
            print(json.dumps(run_drill(name,real=getattr(args,'real',False))))
        return 0
    except (Exception,KeyboardInterrupt) as error:
        print(json.dumps({'passed':False,'error':str(error)}),flush=True)
        return 1
    finally:
        for number,handler in previous.items():
            signal.signal(number,handler)
