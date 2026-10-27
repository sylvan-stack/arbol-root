"""Explicit installed Jensen migration phases; never automatically replay a durable phase."""

from __future__ import annotations

import argparse
import json
import math
import re
import signal
import stat
import time
import uuid
from collections.abc import Callable
from contextlib import closing
from datetime import UTC, datetime
from types import FrameType
from typing import Any

from drill_support import Budget, Inspector, Places, document, new_json, require, wait_for
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
from sapling_messages import judge, usage_available
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


def ready(frame: MigrationFrame) -> dict[str, Any]:
    qualified(frame.places,'open-exchange')
    number = preparing(frame)
    target = Inspector(frame.places,root='jensen')
    source_before = Snapshot(frame.inspector).read()
    target_before = Snapshot(target,provenance=True).read()
    try:
        changed = frame.calls.run('arbol-roots','ready','jensen')
    finally:
        # Adopt only the observed current Root for cleanup, even after an ambiguous command.
        roots = frame.calls.run('arbol-roots','list')
        current = [x['root'] for x in roots if x.get('current')]
        require(len(current) == 1 and current[0] in ('sapling','jensen'), 'Current Root became ambiguous at ready.')
        frame.current = current[0]
    require(changed.get('root') == 'jensen' and changed.get('status') == 'working' and frame.current == 'jensen',
            'Jensen was not made working/current.')
    default = frame.calls.run('arbol-root','list')
    require(default.get('root') == 'jensen' and default.get('rootBuild') == number,
            'The default launcher did not resolve Jensen and its qualified manager.')
    require(fingerprints(Snapshot(frame.inspector).read()) == fingerprints(source_before)
            and fingerprints(Snapshot(target,provenance=True).read()) == fingerprints(target_before),
            'Ready changed database rows.')
    require(frame.calls.run('arbol-roots','show','sapling')['status'] == 'working', 'First Sapling stopped working.')
    probe = frame.root_exchange('sapling','R5').start('First Sapling still works after Jensen becomes current.')
    probe.finish('completed')
    before_refusal = Snapshot(frame.inspector).read()
    record = (frame.places.roots/'jensen/root.json').read_bytes()
    refused = frame.calls.run('arbol-roots','migrate','jensen',status=1)
    require(refused.get('error',{}).get('code') == 'invalid_input', 'Working Jensen migration was not refused.')
    require(fingerprints(Snapshot(frame.inspector).read()) == fingerprints(before_refusal)
            and fingerprints(Snapshot(target,provenance=True).read()) == fingerprints(target_before)
            and (frame.places.roots/'jensen/root.json').read_bytes() == record,
            'Refused migration changed a Root or its rows.')
    return {'root':'jensen','rootBuild':number,'currentRoot':'jensen','defaultRoot':default['root'],
            'sourceProbeExchange':probe.id,'sourceProbeChat':probe.chat,'sourceStillWorking':True,
            'workingMigrationRefused':refused,'ready':changed,'migratedRowsUnchanged':True}


def original_chat(places: Places) -> str:
    proof = document((places.evidence/'SYL-186-real-messages-cost-reconciled.json').read_bytes())
    require(proof.get('passed') is True and proof.get('root') == 'sapling' and len(proof.get('messages',[])) == 2,
            'The original successful real-chat receipt is unavailable.')
    return str(uuid.UUID(proof['chat']))


def chat_history(value: dict[str, Any], chat: str) -> tuple[list[dict[str, Any]],int,str]:
    tables = value['tables']
    exchanges = [x for x in tables['exchanges']['rows'] if x['chat_id'] == chat]
    require(exchanges and all(x['state'] != 'open' for x in exchanges), 'The migrated chat is missing or busy.')
    numbers = {x['id']:x['number'] for x in exchanges if not x['replaced_by']}
    require(not any(x['exchange_id'] in numbers for x in tables['tool_calls']['rows']),
            'The selected real verification chat must have message history only.')
    messages = sorted((x for x in tables['messages']['rows'] if x['exchange_id'] in numbers),
                      key=lambda x:(numbers[x['exchange_id']],x['position']))
    history = [{'type':'message','role':x['role'],'text':x['text']} for x in messages]
    first = next((x['text'] for x in messages if x['role'] == 'user'), '')
    word = re.search(r'verification word for this chat: ([a-z0-9]+)',first)
    require(word is not None, 'The migrated verification word is not in the original saved user message.')
    assert word is not None
    return history,max(x['number'] for x in exchanges)+1,word[1]


def target_preserved(before: dict[str, Any], after: dict[str, Any]) -> bool:
    return all(set(table['encodedRows']) <= set(after['tables'][name]['encodedRows'])
               for name,table in before['tables'].items())


def continuation(frame: MigrationFrame, *, real: bool = False) -> dict[str, Any]:
    qualified(frame.places,'ready')
    if real:
        qualified(frame.places,'continuation')
    chat = original_chat(frame.places)
    target = Inspector(frame.places,root='jensen')
    before = Snapshot(target,provenance=True).read()
    source_before = fingerprints(Snapshot(frame.inspector).read())
    history,number,word = chat_history(before,chat)
    new_json(frame.evidence/'jensen-before-continuation.json',before)
    exchange = frame.root_exchange('jensen',None if real else 'R5',chat)
    budget = Budget(frame.places.evidence)
    if real:
        require(frame.calls.run('arbol-claude-driver','subscriptions','check','anthropic').get('state') == 'signed_in',
                'The normal owner anthropic Subscription is not signed in.')
        require(usage_available(frame.calls.run('arbol-claude-driver','subscriptions','usage','anthropic'),time.time()),
                'Normal owner usage is unavailable or at an unexpired limit; no message was submitted.')
        prior = budget.status()
        require(prior['remaining'] >= 1 and all((x.get('usage') or {}).get('retryNotBeforeUnix',0) <= time.time()
                for x in prior['attempts']), 'The shared budget/retry deadline refuses this real continuation.')
    message = ('What exact verification word did I give you at the beginning of this chat, before the migration? '
               'Reply with that word only.') if real else 'Continue this migrated chat in Jensen Root.'
    new_json(frame.evidence/'submission.json',{'root':'jensen','chat':chat,'exchange':exchange.id,'message':message,
                                            'number':number,'real':real})
    submitted = False
    if real:
        budget.reserve(exchange.id,'SYL-189')
    try:
        submitted = True
        exchange.start(message)
        require(exchange.accepted['number'] == number, 'The migrated chat did not take its next Exchange number.')
        def terminal() -> dict[str, Any] | None:
            value = exchange.persisted()
            row = value.get('exchange') or {}
            return value if row.get('state') in ('completed','failed','cancelled','interrupted') and not exchange.folder.exists() else None
        ended = wait_for(terminal,seconds=300 if real else 35,interval=0.2)
        data = exchange.finish(ended['exchange']['state'])
        if real:
            verdict = judge(data,exchange.accepted,message,number,remembered=word)
            budget.finish(exchange.id,'completed',usage={k:verdict[k] for k in
                                                       ['inputTokens','outputTokens','reportedCostUSD']})
        else:
            assert exchange.fixture is not None
            records = exchange.fixture.records()
            require(len(records) == 1 and records[0]['request'].get('history') == history,
                    'The private Driver did not receive exactly the migrated whole-message history.')
            new_json(frame.evidence/'received-history.json',records)
            verdict = {'historyItems':len(history),'receivedHistoryExact':True}
    except BaseException:
        if real:
            usage = None
            try:
                cause = (exchange.persisted().get('exchange') or {}).get('error') or {}
                retry = cause.get('retryAfterSeconds')
                if (cause.get('code') == 'rate_limited' and isinstance(retry,(int,float))
                        and not isinstance(retry,bool) and math.isfinite(retry) and retry >= 0):
                    usage = {'error':'rate_limited','retryNotBeforeUnix':time.time()+retry}
            except Exception:
                pass
            budget.finish(exchange.id,'ambiguous' if submitted else 'no_vendor',usage=usage)
        raise
    after = Snapshot(target,provenance=True).read()
    new_json(frame.evidence/'jensen-after-continuation.json',after)
    require(target_preserved(before,after) and fingerprints(Snapshot(frame.inspector).read()) == source_before,
            'Continuation changed old Jensen rows or any First Sapling row.')
    frame.preflight(allow_owned=True)
    return {'root':'jensen','chat':chat,'exchange':exchange.id,'number':number,'realMessages':1 if real else 0,
            'oldJensenRowsPreserved':True,'sourceFingerprintUnchanged':True,'verdict':verdict,
            'budget':budget.status() if real else None}


OPERATIONS: dict[str, Callable[[MigrationFrame],dict[str,Any]]] = {'failure':failure,'open-exchange':open_exchange,'ready':ready,'continuation':continuation,
              'real-continuation':lambda frame:continuation(frame,real=True)}


def run_phase(name: str) -> dict[str, Any]:
    places = Places.owner()
    root = places.evidence/'jensen-drills'/name
    require(not list(root.glob('*/qualified.json')), 'This Jensen phase is already qualified; inspect its receipt.')
    frame = MigrationFrame('jensen-'+name,current='jensen' if name in ('continuation','real-continuation') else 'sapling')
    try:
        try:
            details = OPERATIONS[name](frame)
        except BaseException as error:
            new_json(frame.evidence/'failure.json',{'error':str(error),'kind':type(error).__name__})
            raise
    finally:
        frame.close()
    report = {'check':'sapling.jensen-'+name,**frame.proof(),**details,'realMessages':details.get('realMessages',0)}
    receipt = root/frame.evidence.name/'qualified.json'
    new_json(receipt,report)
    new_json(frame.evidence/'qualified.json',report)
    return report


def entry(name: str) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--run',action='store_true')
    if name == 'continuation':
        parser.add_argument('--send',action='store_true')
    args = parser.parse_args()
    if getattr(args,'send',False):
        require(args.run, '--send also requires --run.')
        name = 'real-continuation'
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
