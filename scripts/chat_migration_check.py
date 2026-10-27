"""Exercise advertised check/chat SQL against fictional databases on the check's own server."""

from __future__ import annotations

import copy
import json
import stat
import subprocess
import tempfile
import time
import uuid
from concurrent.futures import ThreadPoolExecutor
from decimal import Decimal
from pathlib import Path
from typing import Any

from scripts.migration_fixtures import CHATS, EXCHANGES, seed
from scripts.migration_protocol import REQUIRED, mode_protocol
from scripts.sql_support import BuildInput, SqlLab

TABLES = ('chats','exchanges','messages','tool_calls','runs','migrated_chats')
type Rows = dict[str,list[dict[str,Any]]]


def history(lab: SqlLab, database: str) -> Rows:
    # PostgreSQL encodes numeric JSON values; Decimal keeps every digit in the comparison.
    return {table:([json.loads(row['value'],parse_float=Decimal) for row in lab.server.rows(database,
                   f'SELECT row_to_json(t)::text AS value FROM {table} t ORDER BY row_to_json(t)::text')]
                   if lab.server.value(database,f"SELECT to_json(to_regclass('public.{table}') IS NOT NULL)") else [])
            for table in TABLES}


def same(expected: Any, actual: Any, detail: str) -> None:
    if expected != actual:
        raise ValueError('Chat migration changed '+detail+'.')


def invoke(lab: SqlLab, inputs: BuildInput, source: str, target: str, mode: str,
           chat: str | None = None, *, extra: dict[str,str] | None = None) -> subprocess.CompletedProcess[str]:
    flag = {'arbol_migrate_check':'1'} if mode == 'check' else {'arbol_migrate_chat':str(chat)} if mode == 'chat' else {}
    allowed = {'progress.copy'} if mode == 'check' else REQUIRED
    with tempfile.TemporaryDirectory(prefix='chat-migration-',dir=lab.server.home) as directory:
        folder = Path(directory)
        same(0o700,stat.S_IMODE(folder.stat().st_mode),'copy directory privacy')
        answer = lab.run_file(target,inputs.file('migrate.sql'),single=False,cwd=folder,check=False,
                              variables={'from_database':source,'from_root':str(inputs.older),**flag,**(extra or {})})
        if any(p.name not in allowed or not stat.S_ISREG(p.lstat().st_mode) for p in folder.iterdir()):
            raise ValueError('Chat migration wrote an unexpected copy file.')
        return answer


def reply(answer: subprocess.CompletedProcess[str], mode: str) -> dict[str,Any]:
    if answer.returncode:
        raise ValueError(f'Chat migration {mode} failed with {answer.returncode}: {answer.stderr.strip()}')
    value = json.loads(answer.stdout)
    if not isinstance(value,dict) or value.get('mode') != mode:
        raise ValueError('Chat migration did not emit one mode result.')
    return value


def chat_rows(values: Rows, chat: str) -> Rows:
    ids = {row['id'] for row in values['exchanges'] if row['chat_id']==chat}
    return {table:[row for row in rows if (row['id']==chat if table=='chats' else row['chat_id']==chat
                 if table in ('exchanges','migrated_chats') else row['exchange_id'] in ids)]
            for table,rows in values.items()}


def copied(source: Rows, target: Rows, original: str, destination: str, result: dict[str,Any]) -> None:
    expected = copy.deepcopy(chat_rows(source,original))
    actual = chat_rows(target,destination)
    same(1,len(actual['chats']),'copied chat count')
    expected['chats'][0]['id'] = destination
    by_number = {row['number']:row for row in actual['exchanges']}
    mapping = {row['id']:by_number[row['number']]['id'] for row in expected['exchanges']}
    for row in expected['exchanges']:
        row['id'],row['chat_id'] = mapping[row['id']],destination
        if row['replaced_by'] is not None:
            row['replaced_by'] = mapping[row['replaced_by']]
        if row['state']=='open':
            row['state'],row['ended_at'] = 'interrupted',result['snapshotAt']
    for table in ['messages','tool_calls','runs']:
        for row in expected[table]:
            row['exchange_id'] = mapping[row['exchange_id']]
    # Sort by stable relational keys, without reserializing or rounding any JSON number.
    for table in TABLES[:-1]:
        def key(row: dict[str,Any], name: str = table) -> tuple[str,...]:
            return (row['id'],) if name in ('chats','exchanges') else (row['exchange_id'],str(row.get('position',row.get('run_id'))))
        same(sorted(expected[table],key=key),sorted(actual[table],key=key),'exact copied '+table+' text/JSON/history')
    provenance = actual['migrated_chats']
    same(1,len(provenance),'provenance count')
    same({'chat_id':destination,'from_root':result['fromRoot'],'from_chat':original,
          'ended_through':result['endedThrough'],'migrated_at':result['snapshotAt'],'stale':False},
         provenance[0],'provenance/snapshot/stale mark')


def check_modes(inputs: BuildInput, lab: SqlLab) -> dict[str,Any]:
    script = inputs.file('migrate.sql').read_text(encoding='utf-8')
    for mode in inputs.modes:
        mode_protocol(script,mode)
    source,target = 'original_'+uuid.uuid4().hex,'copies_'+uuid.uuid4().hex
    for database in [source,target]:
        lab.server.createdb(database)
        lab.run_file(database,inputs.file('chat-tables.sql'))
        if database == target:
            lab.run_file(database,inputs.file('root-tables.sql'))
        else:
            # Source owns only its earlier Root layout. It need not have stale metadata.
            lab.run_file(database,inputs.folder/'roots'/str(inputs.older)/'layout.sql')
    seed(lab.server,source)
    lab.server.execute(source,'UPDATE runs SET usage=usage || \'{"exact":0.123456789012345678901234567890}\'::jsonb')
    whole = invoke(lab,inputs,source,target,'whole')
    if whole.returncode:
        raise ValueError('The optional modes must preserve whole migration: '+whole.stderr)
    initial = history(lab,target)
    value = reply(invoke(lab,inputs,source,target,'check'),'check')
    same({'mode':'check','fromRoot':inputs.older,'checked':2,'stale':[]},value,'initial comparison')
    same(initial,history(lab,target),'an up-to-date comparison beyond marks')

    # Refresh an open original as interrupted history, without ending/changing that original.
    open_source = history(lab,source)
    open_result = reply(invoke(lab,inputs,source,target,'chat',CHATS[0]),'chat')
    same('replaced',open_result['action'],'uncontinued open-snapshot replacement')
    copied(open_source,history(lab,target),CHATS[0],CHATS[0],open_result)
    same(open_source,history(lab,source),'open source snapshot')
    initial = history(lab,target)

    # End the source's open Exchange: the old copy stays interrupted until explicit reimport.
    lab.server.execute(source,f"UPDATE exchanges SET state='completed',ended_at=clock_timestamp() WHERE id='{EXCHANGES[2]}'")
    advanced = history(lab,source)
    value = reply(invoke(lab,inputs,source,target,'check'),'check')
    same([CHATS[0]],value['stale'],'the intended stale copy')
    marked = history(lab,target)
    for table in TABLES[:-1]:
        same(initial[table],marked[table],'comparison-only '+table)
    for row in marked['migrated_chats']:
        prior = next(r for r in initial['migrated_chats'] if r['chat_id']==row['chat_id'])
        same({**prior,'stale':row['chat_id']==CHATS[0]},row,'comparison-only provenance')
    result = reply(invoke(lab,inputs,source,target,'chat',CHATS[0]),'chat')
    same('replaced',result['action'],'uncontinued replacement choice')
    same(CHATS[0],result['resultChat'],'stable original copy identity')
    copied(advanced,history(lab,target),CHATS[0],CHATS[0],result)
    same(chat_rows(initial,CHATS[1]),chat_rows(history(lab,target),CHATS[1]),'unrelated chat')
    repeat = reply(invoke(lab,inputs,source,target,'chat',CHATS[0]),'chat')
    copied(advanced,history(lab,target),CHATS[0],CHATS[0],repeat)

    # Missing/regressed originals cannot clear an existing stale mark or change any row.
    source_end = next(row['ended_at'] for row in advanced['exchanges'] if row['id']==EXCHANGES[2])
    lab.server.execute(source,f"UPDATE exchanges SET state='open',ended_at=NULL WHERE id='{EXCHANGES[2]}'")
    before = history(lab,target)
    same(3,invoke(lab,inputs,source,target,'check').returncode,'regressed-source comparison')
    same(3,invoke(lab,inputs,source,target,'chat',CHATS[0]).returncode,'regressed-source reimport')
    same(before,history(lab,target),'regressed-source rollback')
    lab.server.execute(source,f"UPDATE exchanges SET state='completed',ended_at='{source_end}' WHERE id='{EXCHANGES[2]}'")
    # A source Exchange UUID belonging to unrelated target history is never overwritten.
    lab.server.execute(target,f"UPDATE exchanges SET chat_id='{CHATS[1]}',number=99 WHERE id='{EXCHANGES[2]}'")
    before = history(lab,target)
    same(3,invoke(lab,inputs,source,target,'chat',CHATS[0]).returncode,'unrelated UUID collision')
    same(before,history(lab,target),'UUID-collision rollback')
    lab.server.execute(target,f"UPDATE exchanges SET chat_id='{CHATS[0]}',number=3 WHERE id='{EXCHANGES[2]}'")
    # Cross-chat replacement pointers in the source are refused, never silently dropped.
    lab.server.execute(source,f"UPDATE exchanges SET replaced_by='{EXCHANGES[3]}' WHERE id='{EXCHANGES[1]}'")
    before = history(lab,target)
    same(3,invoke(lab,inputs,source,target,'chat',CHATS[0]).returncode,'cross-chat source replacement')
    same(before,history(lab,target),'cross-chat replacement rollback')
    lab.server.execute(source,f"UPDATE exchanges SET replaced_by='{EXCHANGES[2]}' WHERE id='{EXCHANGES[1]}'")

    # A continued copy keeps all history and its truthful stale flag; even an open target counts.
    local_id = str(uuid.uuid4())
    lab.server.execute(target,f"INSERT INTO exchanges SELECT '{local_id}',chat_id,4,'open',NULL,trunk,build,route,small_call_route,working_folder,clock_timestamp(),NULL,NULL FROM exchanges WHERE id='{EXCHANGES[2]}'")
    lab.server.execute(source,f"INSERT INTO exchanges SELECT '{uuid.uuid4()}',chat_id,4,'completed',NULL,trunk,build,route,small_call_route,working_folder,clock_timestamp(),clock_timestamp(),NULL FROM exchanges WHERE id='{EXCHANGES[2]}'")
    reply(invoke(lab,inputs,source,target,'check'),'check')
    continued = history(lab,target)
    source_now = history(lab,source)
    result = reply(invoke(lab,inputs,source,target,'chat',CHATS[0]),'chat')
    same('copied',result['action'],'continued-copy choice')
    new_chat = result['resultChat']
    if new_chat in CHATS or new_chat == local_id:
        raise ValueError('Continued-copy migration reused an identifier.')
    after_copy = history(lab,target)
    copied(source_now,after_copy,CHATS[0],new_chat,result)
    for old in CHATS:
        same(chat_rows(continued,old),chat_rows(after_copy,old),'preserved continued/unrelated copy')
    source_ids = {row['id'] for row in source_now['exchanges']}
    if source_ids & {row['id'] for row in chat_rows(after_copy,new_chat)['exchanges']}:
        raise ValueError('Continued-copy Exchange UUIDs collided with the original.')
    # Replacing a remapped copy retains its chat UUID and allocates fresh Exchange UUIDs.
    result = reply(invoke(lab,inputs,source,target,'chat',new_chat),'chat')
    same(('replaced',new_chat),(result['action'],result['resultChat']),'remapped replacement identity')
    copied(source_now,history(lab,target),CHATS[0],new_chat,result)
    same(chat_rows(continued,CHATS[0]),chat_rows(history(lab,target),CHATS[0]),'continued copy after remapped replacement')

    # Acceptance that wins the chat row lock is visible after the wait, even though the mode began first.
    race_exchange = str(uuid.uuid4())
    before_race = chat_rows(history(lab,target),new_chat)
    held = lab.server.hold(target,f"DO $$ BEGIN PERFORM 1 FROM chats WHERE id='{new_chat}' FOR UPDATE; "
                           f"INSERT INTO exchanges SELECT '{race_exchange}',chat_id,5,'completed',NULL,trunk,build,route,small_call_route,working_folder,clock_timestamp(),clock_timestamp(),NULL FROM exchanges WHERE chat_id='{new_chat}' ORDER BY number LIMIT 1; END $$")
    try:
        with ThreadPoolExecutor(max_workers=1) as pool:
            future = pool.submit(invoke,lab,inputs,source,target,'chat',new_chat)
            try:
                deadline = time.monotonic()+1.5
                while not lab.server.value(target,"SELECT to_json(EXISTS(SELECT 1 FROM pg_stat_activity "
                                           f"WHERE datname='{target}' AND wait_event_type='Lock'))"):
                    if future.done() or time.monotonic()>=deadline:
                        raise ValueError('The acceptance race never reached the contended target row lock.')
                    time.sleep(0.01)
            finally:
                held.release()
            raced = reply(future.result(timeout=10),'chat')
    finally:
        held.release()
    same('copied',raced['action'],'committed concurrent acceptance choice')
    raced_rows = history(lab,target)
    kept = chat_rows(raced_rows,new_chat)
    for table in TABLES:
        if table=='exchanges':
            same(before_race[table],[row for row in kept[table] if row['id']!=race_exchange],
                 'history before concurrent acceptance')
        else:
            same(before_race[table],kept[table],'concurrent acceptance preserved '+table)
    copied(source_now,raced_rows,CHATS[0],raced['resultChat'],raced)

    # Source missing/regressed and target unknown all refuse atomically with psql status 3.
    for chat in [str(uuid.uuid4()),CHATS[1]]:
        before = history(lab,target)
        if chat==CHATS[1]:
            # Remove the source's unrelated chat's dependent rows in this disposable fixture only.
            lab.server.execute(source,f"DELETE FROM messages WHERE exchange_id='{EXCHANGES[3]}'; DELETE FROM tool_calls WHERE exchange_id='{EXCHANGES[3]}'; DELETE FROM runs WHERE exchange_id='{EXCHANGES[3]}'; DELETE FROM exchanges WHERE id='{EXCHANGES[3]}'; DELETE FROM chats WHERE id='{chat}';")
        answer = invoke(lab,inputs,source,target,'chat',chat)
        same(3,answer.returncode,'unknown-chat status 3')
        if 'Unknown' not in answer.stderr:
            raise ValueError('Unknown target/source did not produce the specific SQL refusal.')
        same(before,history(lab,target),'unknown-chat rollback')
    before = history(lab,target)
    same(3,invoke(lab,inputs,source,target,'check').returncode,'missing-source comparison status')
    same(before,history(lab,target),'missing-source comparison rollback')
    # Lock timeout protects a concurrent accepted chat, without any history write.
    with lab.server.hold(target,f"DO $$ BEGIN PERFORM 1 FROM chats WHERE id='{new_chat}' FOR UPDATE; END $$"):
        answer = invoke(lab,inputs,source,target,'chat',new_chat)
        same(3,answer.returncode,'busy row-lock refusal')
        if 'lock timeout' not in answer.stderr:
            raise ValueError('The concurrent chat did not refuse at its row lock.')
    same(before,history(lab,target),'busy-copy rollback')
    # Both flags must fail before even switching away from the supplied target database.
    same(3,invoke(lab,inputs,'nonexistent_source',target,'chat',new_chat,extra={'arbol_migrate_check':'1'}).returncode,'mutually exclusive flags')
    same(before,history(lab,target),'mutually exclusive refusal')
    # Apart from explicit fixture advancement, no mode has written the source.
    expected_source = chat_rows(source_now,CHATS[0])
    same(expected_source,history(lab,source),'read-only source')
    return {'modes':list(inputs.modes),'staleOnly':True,'exactHistory':True,'uncontinuedReplaced':True,
            'continuedPreserved':True,'remappedReplaced':True,'sourceUnchanged':True,
            'unknownTargetStatus':3,'unknownSourceStatus':3,'busyStatus':3,'bothFlagsStatus':3,
            'regressionRefused':True,'collisionRefused':True,'concurrentAcceptancePreserved':True}
