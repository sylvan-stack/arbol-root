# Test implementations moved to tests/mid/archived/scripts/chat_migration_check.py.
"""Exercise advertised check/chat SQL against fictional databases on the check's own server."""

from __future__ import annotations

import copy
import json
import stat
import subprocess
import tempfile
from decimal import Decimal
from pathlib import Path
from typing import Any

from scripts.migration_protocol import mode_protocol, protocol
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
    script = inputs.file('migrate.sql').read_text(encoding='utf-8')
    allowed = protocol(script) if mode == 'whole' else mode_protocol(script,mode)
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
    raise RuntimeError('Tests are commented under the tier policy; see TESTS.md. Restore only in an explicitly requested testing task.')  # TEST-TIER-REFUSAL


def backend_modes(inputs: BuildInput, lab: SqlLab) -> dict[str,bool]:
    raise RuntimeError('Tests are commented under the tier policy; see TESTS.md. Restore only in an explicitly requested testing task.')  # TEST-TIER-REFUSAL

# Archived complete imports; restore needed names in their original scope, not at this file tail.
