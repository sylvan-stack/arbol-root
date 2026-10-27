"""Explicit Jensen stale/reimport phases; preview by default, never replay a started phase blindly."""

from __future__ import annotations

import argparse
import json
import signal
from datetime import datetime
from types import FrameType
from typing import Any

from drill_support import Inspector, Places, document, new_json, require
from migration_support import TABLES, MigrationFrame, Snapshot, fingerprints
from sapling_creation import merged_source

CHAT = '4ed0471d-bae6-4bb7-81ba-645a6705d8b4'
PHASES = ('layout','replace','diverged')


def selected(value: dict[str, Any], chat: str, *, outside: bool = False) -> dict[str,list[str]]:
    tables = value['tables']
    exchanges = {row['id'] for row in tables['exchanges']['rows'] if row['chat_id']==chat}
    result = {}
    for name,table in tables.items():
        key = 'id' if name=='chats' else 'chat_id' if name in ('exchanges','migrated_chats') else 'exchange_id'
        owned = {chat} if name in ('chats','exchanges','migrated_chats') else exchanges
        result[name] = [encoded for row,encoded in zip(table['rows'],table['encodedRows'],strict=True)
                        if (row[key] in owned) != outside]
    return result


def receipt(places: Places, phase: str) -> dict[str, Any]:
    files = list((places.evidence/'chat-reimport'/phase).glob('*/qualified.json'))
    require(len(files)==1,'Exactly one qualified '+phase+' receipt is required.')
    value = document(files[0].read_bytes())
    require(value.get('passed') is True,'The prior reimport phase did not pass.')
    return dict(value)


def snapshot(frame: MigrationFrame, root: str) -> dict[str, Any]:
    return Snapshot(Inspector(frame.places,root=root),provenance=root=='jensen').read()


def copied(source: dict[str, Any], target: dict[str, Any], chat: str, result: dict[str, Any]) -> None:
    src,dst = selected(source,CHAT),selected(target,chat)
    source_exchanges = [document(row) for row in src['exchanges']]
    target_exchanges = {document(row)['number']:document(row) for row in dst['exchanges']}
    require(len(source_exchanges)==len(target_exchanges) and all(row['state']!='open' for row in source_exchanges),
            'The selected ended source history was incomplete or busy.')
    mapping = {row['id']:target_exchanges[row['number']]['id'] for row in source_exchanges}
    expected = {name:list(rows) for name,rows in src.items()}
    expected['chats'] = [row.replace('{"id":"'+CHAT+'"','{"id":"'+chat+'"',1) for row in src['chats']]
    expected['exchanges'] = []
    for encoded in src['exchanges']:
        row = document(encoded)
        encoded = encoded.replace('{"id":"'+row['id']+'"','{"id":"'+mapping[row['id']]+'"',1)
        encoded = encoded.replace(',"chat_id":"'+CHAT+'"',',"chat_id":"'+chat+'"',1)
        if row['replaced_by'] is not None:
            ending = ',"replaced_by":"'+row['replaced_by']+'"}'
            require(encoded.endswith(ending),'Unexpected Exchange row encoding; refusing a lossy comparison.')
            encoded = encoded[:-len(ending)]+',"replaced_by":"'+mapping[row['replaced_by']]+'"}'
        expected['exchanges'].append(encoded)
    for name in ['messages','tool_calls','runs']:
        expected[name] = [encoded.replace('{"exchange_id":"'+document(encoded)['exchange_id']+'"',
                            '{"exchange_id":"'+mapping[document(encoded)['exchange_id']]+'"',1) for encoded in src[name]]
    for name in TABLES:
        require(sorted(expected[name])==sorted(dst[name]),'Reimport changed exact '+name+' text/JSON/history.')
    provenance = [document(row) for row in dst['migrated_chats']]
    require(len(provenance)==1,'The result chat lacks exactly one provenance row.')
    row = provenance[0]
    ended = max((row['number'] for row in source_exchanges),default=0)
    require(row['chat_id']==chat and row['from_root']=='sapling' and row['from_chat']==CHAT
            and row['ended_through']==ended==result['endedThrough'] and row['stale'] is False
            and datetime.fromisoformat(row['migrated_at'])==datetime.fromisoformat(result['snapshotAt']),
            'The result provenance, cursor, snapshot or stale mark differs.')


def upgrade(frame: MigrationFrame) -> dict[str, Any]:
    source = frame.places.home/'repos/sylvan-stack/readonly/arbol-root'
    commit = merged_source(source)
    catalogue = frame.calls.run('arbol-roots','list')
    before_source,before = snapshot(frame,'sapling'),snapshot(frame,'jensen')
    require(all('stale' not in row for row in before['tables']['migrated_chats']['rows']),
            'The stale layout is already applied; inspect the prior attempt before recovery.')
    built = frame.calls.run('arbol-builds','build','arbol-root','--root','jensen','--repo',str(source),seconds=1200)
    new_json(frame.evidence/'build.json',built)
    require(built.get('status')=='working' and built.get('root')=='jensen'
            and built.get('checks')==[{'name':name,'passed':True} for name in ['unit','layout','migration']]
            and built.get('source',{}).get('commit')==commit and built['source'].get('branch')=='main'
            and built['source'].get('uncommittedChanges') is False,'The newer Jensen Build was not fully qualified from merged source.')
    require(fingerprints(snapshot(frame,'jensen'))==fingerprints(before),'Build checks changed owner target rows.')
    applied = frame.calls.run('arbol-roots','layout','jensen',seconds=90)
    new_json(frame.evidence/'layout.json',applied)
    require(applied.get('rootBuild')==built['build'],'Layout did not select the qualified newer manager.')
    after = snapshot(frame,'jensen')
    for name in TABLES:
        require(before['tables'][name]['encodedRows']==after['tables'][name]['encodedRows'],
                'The additive layout changed old '+name+' rows.')
    require([row[:-1]+',"stale":false}' for row in before['tables']['migrated_chats']['encodedRows']]
            ==after['tables']['migrated_chats']['encodedRows'],'The additive layout changed older provenance beyond stale=false.')
    require(fingerprints(snapshot(frame,'sapling'))==fingerprints(before_source)
            and frame.calls.run('arbol-roots','list')==catalogue,'Upgrade changed the source or catalogue/current Root.')
    new_json(frame.evidence/'target-before.json',before)
    new_json(frame.evidence/'target-after.json',after)
    return {'newRootBuild':built['build'],'sourceCommit':commit,'compatibleLayoutApplied':True,
            'oldRowsPreserved':True,'catalogueUnchanged':True,'sourceUnchanged':True}


def send(frame: MigrationFrame, root: str, message: str) -> str:
    exchange = frame.root_exchange(root,'R5',CHAT).start(message)
    exchange.finish('completed')
    return exchange.id


def replace(frame: MigrationFrame) -> dict[str, Any]:
    receipt(frame.places,'layout')
    before_source,before = snapshot(frame,'sapling'),snapshot(frame,'jensen')
    old = [row for row in before['tables']['migrated_chats']['rows'] if row['chat_id']==CHAT]
    require(len(old)==1 and old[0]['from_root']=='sapling' and old[0]['from_chat']==CHAT
            and old[0]['ended_through']==0,'The selected initial migration cursor differs; inspect before reimport.')
    chosen = [row for row in before['tables']['exchanges']['rows'] if row['chat_id']==CHAT]
    require(chosen and all(row['state']!='open' and datetime.fromisoformat(row['accepted_at'])
            <=datetime.fromisoformat(old[0]['migrated_at']) for row in chosen),'The selected target copy already continued.')
    sent = [send(frame,'sapling','SYL-195 source advancement '+str(number)+'.') for number in [1,2]]
    source = snapshot(frame,'sapling')
    require(selected(before_source,CHAT,outside=True)==selected(source,CHAT,outside=True),'Source messages changed unrelated history.')
    compared = frame.calls.run('arbol-roots','migrate','jensen','--check',seconds=90)
    new_json(frame.evidence/'comparison.json',compared)
    require(compared.get('stale')==[CHAT],'Comparison did not mark only the selected copy stale.')
    marked = snapshot(frame,'jensen')
    for name in TABLES:
        require(before['tables'][name]['encodedRows']==marked['tables'][name]['encodedRows'],
                'Comparison changed target history beyond stale marks.')
    result = frame.calls.run('arbol-roots','migrate','jensen','--chat',CHAT,seconds=90)
    new_json(frame.evidence/'reimport.json',result)
    require(result.get('action')=='replaced' and result.get('resultChat')==CHAT,'The uncontinued copy was not replaced in place.')
    after = snapshot(frame,'jensen')
    copied(source,after,CHAT,result)
    require(selected(before,CHAT,outside=True)==selected(after,CHAT,outside=True),'Replacement changed an unrelated target row.')
    require(fingerprints(snapshot(frame,'sapling'))==fingerprints(source),'Comparison/reimport changed source rows.')
    new_json(frame.evidence/'source.json',source)
    new_json(frame.evidence/'target-before.json',before)
    new_json(frame.evidence/'target-marked.json',marked)
    new_json(frame.evidence/'target-after.json',after)
    return {'chat':CHAT,'sourceExchanges':sent,'result':result,'onlySelectedStale':True,'exactHistory':True,'sourceUnchanged':True}


def diverged(frame: MigrationFrame) -> dict[str, Any]:
    receipt(frame.places,'replace')
    before_source,before = snapshot(frame,'sapling'),snapshot(frame,'jensen')
    local = send(frame,'jensen','SYL-195 keep this Jensen continuation beside a new source copy.')
    source_exchange = send(frame,'sapling','SYL-195 newer original after both copies continue.')
    source,continued = snapshot(frame,'sapling'),snapshot(frame,'jensen')
    require(selected(before_source,CHAT,outside=True)==selected(source,CHAT,outside=True)
            and selected(before,CHAT,outside=True)==selected(continued,CHAT,outside=True),
            'Stand-in advancement changed unrelated history.')
    compared = frame.calls.run('arbol-roots','migrate','jensen','--check',seconds=90)
    require(compared.get('stale')==[CHAT],'Diverged comparison did not mark only the selected copy.')
    marked = snapshot(frame,'jensen')
    result = frame.calls.run('arbol-roots','migrate','jensen','--chat',CHAT,seconds=90)
    new_json(frame.evidence/'reimport.json',result)
    require(result.get('action')=='copied' and result.get('resultChat')!=CHAT,'The continued copy was not preserved beside a new chat.')
    after = snapshot(frame,'jensen')
    copied(source,after,result['resultChat'],result)
    require(selected(after,result['resultChat'],outside=True)=={name:table['encodedRows'] for name,table in marked['tables'].items()},
            'The divergent import changed an old target row or its truthful stale mark.')
    require(fingerprints(snapshot(frame,'sapling'))==fingerprints(source),'Divergent import changed source rows.')
    new_json(frame.evidence/'source.json',source)
    new_json(frame.evidence/'target-marked.json',marked)
    new_json(frame.evidence/'target-after.json',after)
    return {'chat':CHAT,'localExchange':local,'sourceExchange':source_exchange,'result':result,
            'oldTargetRowsPreserved':True,'exactHistory':True,'sourceUnchanged':True}


def run(phase: str) -> dict[str, Any]:
    places = Places.owner()
    folder = places.evidence/'chat-reimport'/phase
    require(not list(folder.glob('*/planned.json')),'This phase was already started; inspect its saved state before recovery.')
    frame = MigrationFrame('chat-reimport-'+phase,current='jensen')
    attempt = folder/frame.evidence.name
    new_json(attempt/'planned.json',{'phase':phase,'chat':CHAT,'evidence':str(frame.evidence),'realMessages':0})
    try:
        try:
            catalogue = frame.calls.run('arbol-roots','list')
            details = {'layout':upgrade,'replace':replace,'diverged':diverged}[phase](frame)
            require(frame.calls.run('arbol-roots','list')==catalogue,'The reimport phase changed Root metadata/current.')
        except BaseException as error:
            new_json(attempt/'failure.json',{'error':str(error),'next':'Inspect saved state; do not replay this phase.'})
            raise
    finally:
        frame.close()
    result = {'check':'sapling.chat-reimport-'+phase,**frame.proof(),**details,'realMessages':0}
    new_json(attempt/'qualified.json',result)
    new_json(frame.evidence/'qualified.json',result)
    return result


def entry() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('phase',choices=PHASES)
    parser.add_argument('--run',action='store_true')
    args = parser.parse_args()
    previous = {number:signal.getsignal(number) for number in (signal.SIGINT,signal.SIGTERM)}
    def interrupted(number: int, _frame: FrameType | None) -> None:
        raise KeyboardInterrupt('Reimport drill interrupted by '+str(number))
    try:
        for number in previous:
            signal.signal(number,interrupted)
        print(json.dumps(run(args.phase) if args.run else {'preflightOnly':True,'phase':args.phase,'chat':CHAT,'realMessages':0}))
        return 0
    except (Exception,KeyboardInterrupt) as error:
        print(json.dumps({'passed':False,'error':str(error)}))
        return 1
    finally:
        for number,handler in previous.items():
            signal.signal(number,handler)
