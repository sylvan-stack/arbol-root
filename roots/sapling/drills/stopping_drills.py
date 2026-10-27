"""Real-timing installed stop and compatible-manager drills, using only private stand-ins."""

from __future__ import annotations

import argparse
import fcntl
import json
import os
import signal
from collections.abc import Callable
from pathlib import Path
from types import FrameType
from typing import Any

from drill_support import document, new_json, require, wait_for
from sapling_creation import merged_source
from sapling_outage import stopped
from stopping_support import Manager, freeze_exchange, ignored_child, stop_state, wait_ignored_child, wait_stop
from trunk_drill_support import Frame
from trunk_drills import judge_database_rows, resume, tool_rows


def obeyed(frame: Frame) -> dict[str, Any]:
    exchange = frame.exchange('R10').start()
    exchange.event('tool_started')
    exchange.capture_processes()
    control = (exchange.folder/'control').open('rb')
    manager = Manager(frame,['stop',exchange.id],'stop')
    try:
        result = manager.finish()
        stop_state(result,'cancelled',forced=False)
        data = exchange.finish('cancelled')
        lines = [document(line) for line in control.read().splitlines()]
        require(lines == [{'type':'stop'}], 'The graceful command did not append exactly one stop line.')
    finally:
        manager.close()
        control.close()
    calls = tool_rows(exchange)
    require(len(calls) == 1 and calls[0]['interrupted'] is True and data['runs'][0]['outcome'] == 'cancelled',
            'The graceful stop lost the interrupted open call or cancelled run.')
    following = resume(frame,exchange)
    return {'exchange':exchange.id,'manager':result,'continuedExchange':following['exchange']['id']}


def not_obeyed(frame: Frame) -> dict[str, Any]:
    exchange = frame.exchange('R10').start()
    exchange.event('tool_started')
    with freeze_exchange(exchange,'freeze.json'):
        manager = Manager(frame,['stop',exchange.id],'stop')
        try:
            result = manager.finish(seconds=40)
            stop_state(result,'interrupted',forced=True)
            require(19.5 <= result['elapsedSeconds'] <= 34, 'The real twenty-second graceful deadline was not observed.')
            exchange.finish('interrupted')
        finally:
            manager.close()
    following = resume(frame,exchange)
    return {'exchange':exchange.id,'manager':result,'continuedExchange':following['exchange']['id']}


def end_already_written(frame: Frame) -> dict[str, Any]:
    exchange = frame.exchange('R12 end').start()
    exchange.event('text')
    frame.preflight(allow_owned=True)
    assert exchange.fixture is not None
    with stopped(stop=frame.service.stop,restore=frame.service.restore,healthy=frame.service.healthy,
                 receipt=frame.evidence/'restoration.json'):
        exchange.fixture.release()
        end = wait_for(lambda:exchange.record().get('end'),seconds=20)
        with freeze_exchange(exchange,'freeze.json'):
            # Restore while the owned Trunk is frozen. The outer guard also restores after any failure.
            frame.service.restore()
            wait_for(lambda:True if frame.service.healthy() else None,seconds=30,interval=0.2)
            require(end['state'] == 'completed' and exchange.listing_state() == 'ending',
                    'The frozen Trunk did not retain its known completed ending state.')
            control_before = (exchange.folder/'control').read_bytes()
            manager = Manager(frame,['stop',exchange.id],'stop')
            try:
                result = manager.finish(seconds=10)
                require(result['reply'].get('ended') == 'completed' and result['reply'].get('forced') is False,
                        'An already-written live end was forced or misreported.')
                require(result['elapsedSeconds'] < 8 and (exchange.folder/'control').read_bytes() == control_before,
                        'Stop of an already-ended record waited or appended a new stop.')
            finally:
                manager.close()
    exchange.finish('completed')
    judge_database_rows(exchange)
    return {'exchange':exchange.id,'manager':result,'knownEndPreserved':True}


def force(frame: Frame, *, stubborn: bool = False) -> dict[str, Any]:
    exchange = frame.exchange('R10')
    if stubborn:
        ignored_child(exchange)
    exchange.start()
    exchange.event('tool_started')
    if stubborn:
        wait_ignored_child(exchange)
    else:
        exchange.capture_processes()
    manager = Manager(frame,['stop','--force',exchange.id],'stop')
    try:
        result = manager.finish(seconds=25)
        stop_state(result,'interrupted',forced=True)
        exchange.finish('interrupted')
    finally:
        manager.close()
    if stubborn:
        assert exchange.fixture is not None
        signals = [document(line) for line in
                   (exchange.fixture.home/'standin/ignored-signals.jsonl').read_bytes().splitlines()]
        require(any(row['signal'] == signal.SIGTERM for row in signals), 'The ignored child never saw SIGTERM.')
        require(4.5 <= result['elapsedSeconds'] <= 16, 'The real five-second force grace was not observed.')
        new_json(frame.evidence/'ignored-term-events.json',signals)
    return {'exchange':exchange.id,'manager':result,'ignoredTermChild':stubborn,'allOwnedProcessesGone':exchange.gone()}


def killed_while_waiting(frame: Frame) -> dict[str, Any]:
    exchange = frame.exchange('R10').start()
    exchange.event('tool_started')
    with freeze_exchange(exchange,'freeze.json'):
        original = exchange.record()
        manager = Manager(frame,['stop',exchange.id],'first-stop')
        try:
            wait_stop(exchange)
            manager.kill()
        finally:
            manager.close()
        require(exchange.record() == original and exchange.listing_state() == 'running',
                'Killing the waiting command changed the live frozen record or its listing.')
        following = Manager(frame,['stop',exchange.id],'next-stop')
        try:
            result = following.finish(seconds=40)
            stop_state(result,'interrupted',forced=True)
            exchange.finish('interrupted')
        finally:
            following.close()
    resume(frame,exchange)
    return {'exchange':exchange.id,'nextManager':result,'killedPhase':'waiting'}


def killed_while_forcing(frame: Frame) -> dict[str, Any]:
    exchange = frame.exchange('R10')
    ignored_child(exchange)
    exchange.start()
    exchange.event('tool_started')
    child = wait_ignored_child(exchange)
    assert exchange.fixture is not None
    marker = exchange.fixture.home/'standin/ignored-signals.jsonl'
    manager = Manager(frame,['stop','--force',exchange.id],'first-stop')
    try:
        wait_for(lambda:True if marker.exists() else None,seconds=10,interval=0.02)
        manager.kill()
    finally:
        manager.close()
    require(not exchange.gone(), 'Nothing remained in the planned force interruption window.')
    require(exchange.listing_state() in ('running','ending'), 'The next listing lost the interrupted forcing work.')
    following = Manager(frame,['stop','--force',exchange.id],'next-stop')
    try:
        result = following.finish(seconds=25)
        stop_state(result,'interrupted',forced=True)
        exchange.finish('interrupted')
    finally:
        following.close()
    return {'exchange':exchange.id,'ignoredChild':child['pid'],'nextManager':result,'killedPhase':'forcing'}


def build_journal(frame: Frame) -> Path:
    return frame.places.evidence/'stopping-drills/newer-build-receipts.jsonl'


def reuse_build(frame: Frame) -> dict[str, Any]:
    journal = build_journal(frame)
    require(journal.is_file(), 'No qualified newer-manager receipt exists; run its explicit build drill first.')
    lines = journal.read_bytes().splitlines()
    require(lines, 'The newer-manager receipt journal is empty.')
    receipt = document(lines[-1])
    report = document(Path(receipt['report']).read_bytes())
    require(report.get('passed') is True and report.get('check') == 'sapling.newer-build',
            'The newer-manager receipt was not a passing complete drill.')
    number = report['newRootBuild']
    folder = frame.places.home/'Library/Application Support/Arbol/builds/arbol-root'/number
    record = document((folder/'build.json').read_bytes())
    checks = [{'name':name,'passed':True} for name in ['unit','layout','migration']]
    require(record.get('component') == 'arbol-root' and record.get('build') == number
            and record.get('status') == 'working' and record.get('root') == 'sapling'
            and record.get('source') == report['built']['source']
            and record.get('checks') == checks and report['built']['checks'] == checks,
            'The retained newer manager no longer matches its qualified source/checks/status.')
    listing = frame.calls.run('arbol-root','--root','sapling','list')
    require(listing['rootBuild'] == number, 'The qualified newer manager is no longer the chosen Build.')
    return {'qualifiedReceipt':receipt['report'],'newRootBuild':number,'reusedQualifiedBuild':True}


def newer_build(frame: Frame) -> dict[str, Any]:
    source = frame.places.home/'repos/sylvan-stack/readonly/arbol-root'
    commit = merged_source(source)
    catalogue = frame.calls.run('arbol-roots','list')
    root_record = (frame.places.roots/'sapling/root.json').read_bytes()
    before_listing = frame.calls.run('arbol-root','--root','sapling','list')
    old_number = before_listing['rootBuild']
    exchange = frame.exchange('R10').start()
    exchange.event('tool_started')
    accepted = dict(exchange.accepted)
    built = frame.calls.run('arbol-builds','build','arbol-root','--root','sapling','--repo',str(source),seconds=1200)
    new_json(frame.evidence/'built.json',built)
    require(built.get('status') == 'working' and built.get('root') == 'sapling'
            and int(built['build'],16) > int(old_number,16)
            and built.get('checks') == [{'name':name,'passed':True} for name in ['unit','layout','migration']],
            'The newer manager did not pass all three actual packaged checks.')
    require(built.get('source',{}).get('commit') == commit and built['source'].get('branch') == 'main'
            and built['source'].get('uncommittedChanges') is False,
            'The newer manager did not use the exact clean merged readonly source.')
    listing = frame.calls.run('arbol-root','--root','sapling','list')
    row = next(value for value in listing['exchanges'] if value['exchange'] == exchange.id)
    require(listing['rootBuild'] == built['build'] and all(row[key] == accepted[key] for key in
            ['root','exchange','chat','trunk','build']), 'The newer manager changed the accepted Exchange ownership.')
    require(frame.calls.run('arbol-roots','list') == catalogue
            and (frame.places.roots/'sapling/root.json').read_bytes() == root_record,
            'Making a newer manager changed the Root record/current catalogue.')
    manager = Manager(frame,['stop',exchange.id],'newer-stop')
    try:
        result = manager.finish()
        stop_state(result,'cancelled',forced=False)
        exchange.finish('cancelled')
    finally:
        manager.close()
    killed = frame.exchange('R13 interrupted').start()
    killed.event('usage')
    killed.kill_trunk()
    wait_for(lambda:True if killed.gone() else None,seconds=25)
    killed.settle('interrupted')
    require(frame.calls.run('arbol-root','--root','sapling','list')['rootBuild'] == built['build']
            and frame.calls.run('arbol-roots','list') == catalogue
            and (frame.places.roots/'sapling/root.json').read_bytes() == root_record,
            'The newer stop/settle changed the Root identity or selection.')
    return {'newRootBuild':built['build'],'oldRootBuild':old_number,'built':built,'sourceCommit':commit,
            'stoppedExchange':exchange.id,'settledExchange':killed.id}


DRILLS: dict[str, Callable[[Frame], dict[str, Any]]] = {
    'stop-obeyed':obeyed,'stop-not-obeyed':not_obeyed,'stop-end-already-written':end_already_written,
    'stop-force':force,'stop-force-ignored-term':lambda frame:force(frame,stubborn=True),
    'root-killed-while-waiting':killed_while_waiting,'root-killed-while-forcing':killed_while_forcing,
    'newer-build':newer_build}


def run_drill(name: str, *, reuse_qualified: bool = False) -> dict[str, Any]:
    require(name in DRILLS, 'Unknown stopping drill.')
    frame = Frame(name)
    try:
        try:
            details = reuse_build(frame) if name == 'newer-build' and reuse_qualified else DRILLS[name](frame)
        except BaseException as error:
            new_json(frame.evidence/'failure.json',{'error':str(error),'kind':type(error).__name__})
            raise
    finally:
        frame.close()
    report = {'check':'sapling.'+name,**frame.proof(),**details,'realMessages':0}
    target = frame.evidence/'qualified.json'
    new_json(target,report)
    if name == 'newer-build' and not reuse_qualified:
        journal = build_journal(frame)
        journal.parent.mkdir(parents=True,exist_ok=True,mode=0o700)
        fd = os.open(journal,os.O_WRONLY | os.O_APPEND | os.O_CREAT | os.O_NOFOLLOW,0o600)
        try:
            fcntl.flock(fd,fcntl.LOCK_EX)
            value = (json.dumps({'report':str(target)})+'\n').encode()
            require(os.write(fd,value) == len(value), 'The newer-manager receipt was not fully recorded.')
            os.fsync(fd)
        finally:
            os.close(fd)
    return report


def entry(name: str) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--run',action='store_true')
    if name == 'newer-build':
        parser.add_argument('--reuse-qualified',action='store_true')
    args = parser.parse_args()
    previous = {n:signal.getsignal(n) for n in (signal.SIGINT,signal.SIGTERM)}

    def interrupt(number: int, frame: FrameType | None) -> None:
        raise KeyboardInterrupt('Stopping drill interrupted by signal '+str(number))

    try:
        for number in previous:
            signal.signal(number,interrupt)
        if not args.run:
            print(json.dumps({'preflightOnly':True,'drill':name,'realMessages':0}))
        elif name == 'all':
            for selected in DRILLS:
                print(json.dumps(run_drill(selected,reuse_qualified=selected == 'newer-build')),flush=True)
            print(json.dumps({'check':'sapling.stopping-drills','passed':True,'drills':len(DRILLS),'realMessages':0}))
        else:
            print(json.dumps(run_drill(name,reuse_qualified=getattr(args,'reuse_qualified',False))))
        return 0
    except (Exception,KeyboardInterrupt) as error:
        print(json.dumps({'passed':False,'error':str(error)}),flush=True)
        return 1
    finally:
        for number,handler in previous.items():
            signal.signal(number,handler)
