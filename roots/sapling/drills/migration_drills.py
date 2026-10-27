"""Explicit installed Jensen migration phases; never automatically replay a durable phase."""

from __future__ import annotations

import argparse
import json
import signal
import stat
from contextlib import closing
from datetime import UTC, datetime
from types import FrameType
from typing import Any

from drill_support import Inspector, Places, document, new_json, require, wait_for
from migration_support import (
    TABLES,
    Command,
    MigrationFrame,
    Snapshot,
    SourceLock,
    client_folder,
    fingerprints,
    thaw_client,
)
from sapling_outage import stopped
from stopping_support import frozen
from trunk_drill_support import verify_process


def qualified(places: Places, phase: str) -> dict[str, Any]:
    root = places.evidence/('second-root-attempts' if phase == 'created' else 'jensen-drills/'+phase)
    values = [document(p.read_bytes()) for p in root.glob('*/qualified.json')]
    require(len(values) == 1 and values[0].get('passed') is True, 'Exactly one complete '+phase+' receipt is required.')
    return dict(values[0])


def preparing(frame: MigrationFrame) -> str:
    created = qualified(frame.places,'created')
    record = frame.calls.run('arbol-roots','show','jensen')
    require(record.get('root') == 'jensen' and record.get('name') == 'Jensen Root'
            and record.get('status') == 'preparing' and record.get('grewFrom') == 'sapling'
            and record.get('rootContract') == 1, 'Jensen is not the expected preparing Root.')
    number = created['rootBuild']
    folder = frame.places.home/'Library/Application Support/Arbol/builds/arbol-root'/number
    build = document((folder/'build.json').read_bytes())
    require(build.get('root') == 'jensen' and build.get('status') == 'working'
            and build.get('checks') == created['built']['checks'] and build.get('source') == created['built']['source'],
            'The retained Jensen manager no longer matches its qualified Build.')
    require(frame.calls.run('arbol-root','--root','jensen','list')['rootBuild'] == number,
            'The qualified Jensen manager is not selected.')
    return str(number)


def failure(frame: MigrationFrame) -> dict[str, Any]:
    number = preparing(frame)
    before = Snapshot(frame.inspector).read()
    catalogue = frame.calls.run('arbol-roots','list')
    new_json(frame.evidence/'source-before.json',before)
    frame.preflight()
    with closing(SourceLock(frame.inspector,frame.evidence)) as lock:
        with closing(Command(frame,['migrate','jensen'],'migration')) as command:
            blocked = wait_for(lock.blocked_copy,seconds=20,interval=0.2)
            child = wait_for(command.psql,seconds=5)
            copy_folder = client_folder(child)
            require(copy_folder.name.startswith('arbol-root-migration-') and copy_folder.is_dir()
                    and stat.S_IMODE(copy_folder.stat().st_mode) == 0o700, 'The migration copy folder is not private.')
            new_json(frame.evidence/'observed-copy.json',{'server':blocked,
                'client':{**child,'started':child['started'].isoformat()},'ownedParent':command.process.pid,'copyFolder':str(copy_folder)})
            with frozen(child,frame.evidence/'freeze.json'):
                with stopped(stop=frame.service.stop,restore=frame.service.restore,healthy=frame.service.healthy,
                             receipt=frame.evidence/'restoration.json'):
                    thaw_client(child)
                    refused = command.finish(status=1,seconds=15)
                    require(refused['reply'].get('error',{}).get('code') == 'database_unavailable',
                            'The interrupted migration did not name its database failure.')
    require(not copy_folder.exists(), 'The failed migration left its owned copy folder.')
    after = Snapshot(frame.inspector).read()
    target = Snapshot(Inspector(frame.places,root='jensen'),provenance=True).read()
    new_json(frame.evidence/'source-after.json',after)
    new_json(frame.evidence/'empty-destination.json',target)
    require(fingerprints(after) == fingerprints(before), 'The intentional failed migration changed source rows.')
    require(all(table['count'] == 0 for table in target['tables'].values()),
            'The intentional failed migration left a destination row.')
    require(frame.calls.run('arbol-roots','list') == catalogue, 'The failed migration changed Root records/current.')
    return {'root':'jensen','rootBuild':number,'refusal':refused,'destinationEmpty':True,
            'sourceFingerprintUnchanged':True,'currentRoot':'sapling','status':'preparing'}


def judge_copy(source: dict[str, Any], target: dict[str, Any], began: datetime, ended: datetime) -> dict[str, Any]:
    src,dst = source['tables'],target['tables']
    for name in TABLES:
        if name != 'exchanges':
            require(src[name]['encodedRows'] == dst[name]['encodedRows'], 'Migration changed exact '+name+' rows.')
    originals = {row['id']:row for row in src['exchanges']['rows']}
    copied = {row['id']:row for row in dst['exchanges']['rows']}
    require(set(originals) == set(copied), 'Migration lost or added an Exchange.')
    origin_rows = dst['migrated_chats']['rows']
    chats = {row['id'] for row in src['chats']['rows']}
    require({row['chat_id'] for row in origin_rows} == chats and len(origin_rows) == len(chats),
            'Migration provenance does not cover every chat exactly once.')
    times = {row['migrated_at'] for row in origin_rows}
    require(len(times) == 1, 'Migration provenance did not share one snapshot time.')
    at = str(next(iter(times)))
    snapshot = datetime.fromisoformat(at)
    require(began <= snapshot <= ended, 'The migration snapshot is outside the actual command interval.')
    opened = []
    for key,row in originals.items():
        expected = {**row,'state':'interrupted','ended_at':at} if row['state'] == 'open' else row
        require(copied[key] == expected, 'Migration changed an Exchange beyond its prescribed open snapshot.')
        if row['state'] == 'open':
            opened.append(key)
    for row in origin_rows:
        require(row['from_root'] == 'sapling' and row['from_chat'] == row['chat_id'], 'Wrong migration origin.')
        last = max((item['number'] for item in originals.values()
                    if item['chat_id'] == row['chat_id'] and item['state'] != 'open'),default=0)
        require(row['ended_through'] == last, 'Migration ended_through includes open work or misses history.')
    return {'chats':len(chats),'openExchanges':opened,'snapshotAt':at,'unchangedTables':len(TABLES)-1}


def open_exchange(frame: MigrationFrame) -> dict[str, Any]:
    qualified(frame.places,'failure')
    number = preparing(frame)
    exchange = frame.exchange('R12 end').start('Jensen migration snapshot: original remains in First Sapling.')
    exchange.event('text')
    wait_for(lambda:True if any(x.get('role') == 'assistant' for x in exchange.persisted()['messages']) else None,
             seconds=15,interval=0.1)
    identity = verify_process(exchange.record())
    accepted = dict(exchange.accepted)
    source = Snapshot(frame.inspector).read()
    new_json(frame.evidence/'source-snapshot.json',source)
    require(next(x for x in source['tables']['exchanges']['rows'] if x['id'] == exchange.id)['state'] == 'open',
            'The original Exchange was not open at the saved checkpoint.')
    frame.preflight(allow_owned=True)
    began = datetime.now(UTC)
    migrated = frame.calls.run('arbol-roots','migrate','jensen',seconds=180)
    ended = datetime.now(UTC)
    require(migrated.get('root') == 'jensen' and migrated.get('rootBuild') == number,
            'The successful migration used a different Root/Build.')
    target_inspector = Inspector(frame.places,root='jensen')
    target = Snapshot(target_inspector,provenance=True).read()
    new_json(frame.evidence/'destination-snapshot.json',target)
    judgment = judge_copy(source,target,began,ended)
    require(judgment['openExchanges'] == [exchange.id], 'The migration did not copy exactly the owned open Exchange.')
    require(fingerprints(Snapshot(frame.inspector).read()) == fingerprints(source)
            and verify_process(exchange.record()) == identity and exchange.accepted == accepted
            and exchange.listing_state() == 'running', 'Migration changed the live source/process/ownership.')
    require(not any((frame.places.roots/'jensen/exchanges').iterdir()), 'Migration started an Exchange in Jensen.')
    assert exchange.fixture is not None
    exchange.fixture.release()
    exchange.finish('completed')
    after = Snapshot(frame.inspector).read()
    new_json(frame.evidence/'source-after-original-finished.json',after)
    require(fingerprints(Snapshot(target_inspector,provenance=True).read()) == fingerprints(target),
            'The original completion changed the target history snapshot.')
    # Only this new Exchange may advance after the source checkpoint; all older rows remain exact.
    for name in TABLES:
        column = 'id' if name == 'exchanges' else 'exchange_id'
        if name == 'chats':
            require(source['tables'][name]['encodedRows'] == after['tables'][name]['encodedRows'],
                    'Completing the original changed a chat row.')
            continue
        old = [(encoded,row) for encoded,row in zip(source['tables'][name]['encodedRows'],
                                                   source['tables'][name]['rows'],strict=True) if row[column] != exchange.id]
        later = [(encoded,row) for encoded,row in zip(after['tables'][name]['encodedRows'],
                                                     after['tables'][name]['rows'],strict=True) if row[column] != exchange.id]
        require(old == later, 'Completing the original changed unrelated source '+name+' rows.')
    return {'root':'jensen','rootBuild':number,'sourceExchange':exchange.id,'sourceChat':accepted['chat'],
            'sourceOriginalCompleted':True,'targetSnapshotUnchanged':True,'migrated':migrated,**judgment}


OPERATIONS = {'failure':failure,'open-exchange':open_exchange}


def run_phase(name: str) -> dict[str, Any]:
    places = Places.owner()
    root = places.evidence/'jensen-drills'/name
    require(not list(root.glob('*/qualified.json')), 'This Jensen phase is already qualified; inspect its receipt.')
    frame = MigrationFrame('jensen-'+name)
    try:
        try:
            details = OPERATIONS[name](frame)
        except BaseException as error:
            new_json(frame.evidence/'failure.json',{'error':str(error),'kind':type(error).__name__})
            raise
    finally:
        frame.close()
    report = {'check':'sapling.jensen-'+name,**frame.proof(),**details,'realMessages':0}
    receipt = root/frame.evidence.name/'qualified.json'
    new_json(receipt,report)
    new_json(frame.evidence/'qualified.json',report)
    return report


def entry(name: str) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--run',action='store_true')
    args = parser.parse_args()
    previous = {n:signal.getsignal(n) for n in (signal.SIGINT,signal.SIGTERM)}
    def interrupted(number: int, frame: FrameType | None) -> None:
        raise KeyboardInterrupt('Jensen drill interrupted by signal '+str(number))
    try:
        for number in previous:
            signal.signal(number,interrupted)
        print(json.dumps(run_phase(name) if args.run else {'preflightOnly':True,'phase':name,'realMessages':0}))
        return 0
    except (Exception,KeyboardInterrupt) as error:
        print(json.dumps({'passed':False,'error':str(error)}))
        return 1
    finally:
        for number,handler in previous.items():
            signal.signal(number,handler)
