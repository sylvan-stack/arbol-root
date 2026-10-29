"""Qualify copied migration SQL with fictional history on one disposable server."""

from __future__ import annotations
import uuid


import copy
import json
import stat
import subprocess
import sys
import tempfile
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
sys.path.insert(0,str(ROOT / 'src'))
sys.path.insert(0,str(ROOT / 'contract/conformance'))
from rct_conformance.postgres import SqlError  # noqa: E402
from rct_conformance.tables import catalog  # noqa: E402
from scripts.backend_tables import counter, next_draft, present  # noqa: E402
from scripts.backend_tables import rows as backend_rows  # noqa: E402
from scripts.chat_migration_check import check_modes  # noqa: E402
from scripts.migration_fixtures import seed  # noqa: E402
from scripts.migration_protocol import mode_protocol, protocol  # noqa: E402
from scripts.package_support import verify  # noqa: E402
from scripts.sql_statements import layout_statements  # noqa: E402
from scripts.sql_support import BuildInput, SqlLab, private_server, regular  # noqa: E402


from arbol_root.model import object_file  # noqa: E402
from arbol_root.process import timestamp  # noqa: E402
from scripts.layout_compatibility import TABLES  # noqa: E402
from scripts.sql_support import BuildInput, SqlLab, regular  # noqa: E402

type Rows = dict[str,list[dict[str,Any]]]


@dataclass(frozen=True)
class Origin:
    root: str
    contract: int
    chat: Path
    own: Path


def origin(inputs: BuildInput, home: Path) -> Origin:
    assert inputs.older is not None
    header = object_file(home / 'Library/Application Support/Arbol/roots' / inputs.older / 'root.json')
    version = header.get('rootContract')
    if header.get('root') != inputs.older or type(version) is not int or version < 1:
        raise ValueError('The older Root must have a matching header and positive Root Contract version.')
    return Origin(inputs.older,version,
                  regular(inputs.folder / 'contract' / str(version) / 'layout.sql'),
                  regular(inputs.folder / 'roots' / inputs.older / 'layout.sql'))


def rows(lab: SqlLab, database: str) -> Rows:
    return {entry['table']:lab.server.rows(database,'SELECT * FROM '+entry['table']+' t ORDER BY to_jsonb(t)::text')
            for entry in lab.server.rows(database,TABLES)}


def canonical(values: list[dict[str,Any]]) -> list[str]:
    return sorted(json.dumps(value,sort_keys=True,ensure_ascii=False) for value in values)


def unchanged(expected: Rows, actual: Rows) -> None:
    if set(expected) != set(actual) or any(canonical(expected[name]) != canonical(actual[name]) for name in expected):
        raise ValueError('The older database rows were changed.')


def judge(before: Rows, after: Rows, older: str, started: datetime, finished: datetime) -> set[str]:
    migrated = after.get('public.migrated_chats',[])
    chats, exchanges = before['public.chats'], before['public.exchanges']
    if len(migrated) != len(chats) or not migrated:
        raise ValueError('migrated_chats must have one row per fictional chat.')
    snapshot = migrated[0].get('migrated_at')
    moment = timestamp(snapshot)
    if not started <= moment <= finished:
        raise ValueError('The migration snapshot is outside its actual run interval.')
    by_chat = {entry.get('chat_id'):entry for entry in migrated}
    if len(by_chat) != len(chats):
        raise ValueError('Migration provenance repeated a chat.')
    for chat in chats:
        entry = by_chat.get(chat['id'],{})
        ended = max((value['number'] for value in exchanges
                     if value['chat_id']==chat['id'] and value['state']!='open'),default=0)
        if (entry.get('from_root') != older or entry.get('from_chat') != chat['id']
                or entry.get('ended_through') != ended or entry.get('migrated_at') != snapshot):
            raise ValueError('Migration provenance lost Root/chat/snapshot or ended_through identity.')
    opened = {value['id'] for value in exchanges if value['state']=='open'}
    expected = copy.deepcopy(before)
    for value in expected['public.exchanges']:
        if value['id'] in opened:
            value['state'],value['ended_at'] = 'interrupted',snapshot
    for name, values in expected.items():
        if name not in after or canonical(values) != canonical(after[name]):
            raise ValueError(f'Migration changed unchanged rows, identifiers or exact text/JSON in {name}.')
    return opened


def normalized(values: Rows, opened: set[str]) -> dict[str,list[str]]:
    copied = copy.deepcopy(values)
    for entry in copied.get('public.migrated_chats',[]):
        entry['migrated_at'] = '<snapshot>'
    for entry in copied.get('public.exchanges',[]):
        if entry['id'] in opened:
            entry['ended_at'] = '<snapshot>'
    return {name:canonical(items) for name,items in copied.items()}


def invoke(lab: SqlLab, inputs: BuildInput, source: str, target: str, names: set[str]) -> subprocess.CompletedProcess[str]:
    with tempfile.TemporaryDirectory(prefix='migration-',dir=lab.server.home) as temporary:
        folder = Path(temporary)
        if stat.S_IMODE(folder.stat().st_mode) != 0o700:
            raise ValueError('The migration working directory must be private (0700).')
        answer = lab.run_file(target,inputs.file('migrate.sql'),
                              variables={'from_database':source,'from_root':str(inputs.older)},
                              cwd=folder,single=False,check=False)
        for entry in folder.iterdir():
            if entry.name not in names or not stat.S_ISREG(entry.lstat().st_mode):
                raise ValueError('Migration wrote something outside its allowed regular binary-copy files.')
        return answer


def run_migration(inputs: BuildInput, lab: SqlLab, older: Origin) -> dict[str,Any]:
    names = protocol(inputs.file('migrate.sql').read_text(encoding='utf-8'))
    source = 'from_'+uuid.uuid4().hex
    lab.server.createdb(source)
    for file in [older.chat,older.own]:
        layout_statements(file.read_text(encoding='utf-8'))
        lab.run_file(source,file)
    seed(lab.server,source)
    before, source_schema = rows(lab,source),catalog(lab.server,source)
    source_counter = counter(lab.server,source) if present(lab.server,source) else None
    original_backend = backend_rows(lab.server,source) if source_counter is not None else None
    revisions: list[int] = []

    # A server-side refusal plus the validated source protocol checks READ ONLY independently of row comparison.
    probe = lab.server.home / 'read-only.sql'
    probe.write_text('BEGIN ISOLATION LEVEL REPEATABLE READ READ ONLY;\nUPDATE chats SET title=title;\nCOMMIT;\n')
    refused = lab.run_file(source,probe,single=False,check=False)
    probe.unlink()
    if refused.returncode != 3 or 'read-only' not in refused.stderr:
        raise ValueError('The private READ ONLY write probe did not refuse with status 3.')
    unchanged(before,rows(lab,source))

    def target() -> str:
        database = 'to_'+uuid.uuid4().hex
        lab.server.createdb(database)
        for name in ['chat-tables.sql','root-tables.sql']:
            file = inputs.file(name)
            layout_statements(file.read_text(encoding='utf-8'))
            lab.run_file(database,file)
        return database

    def success() -> tuple[Rows,set[str]]:
        database = target()
        shape = catalog(lab.server,database)
        began = timestamp(lab.server.value(source,'SELECT to_json(clock_timestamp())'))
        answer = invoke(lab,inputs,source,database,names)
        ended = timestamp(lab.server.value(database,'SELECT to_json(clock_timestamp())'))
        if answer.returncode:
            raise ValueError(f'psql migration ended with {answer.returncode}: {answer.stderr.strip()}')
        unchanged(before,rows(lab,source))
        if source_counter is not None and counter(lab.server,source) != source_counter:
            raise ValueError('Whole migration changed the original Draft counter.')
        if original_backend is not None and (backend_rows(lab.server,source) != original_backend
                                            or backend_rows(lab.server,database) != original_backend):
            raise ValueError('Whole migration changed exact backend text/JSON/rows.')
        if catalog(lab.server,source) != source_schema or catalog(lab.server,database) != shape:
            raise ValueError('Migration changed a source or destination table layout.')
        actual = rows(lab,database)
        opened = judge(before,actual,older.root,began,ended)
        if source_counter is not None:
            revisions.append(next_draft(lab.server,database,source_counter,
                                       max(row['revision'] for row in before['public.drafts'])))
        return actual,opened

    first,opened = success()
    for missing in ['source','table']:
        database = target()
        target_counter = counter(lab.server,database) if source_counter is not None else None
        from_database = source
        if missing == 'source':
            from_database = 'absent_'+uuid.uuid4().hex
        else:
            lab.server.execute(database,'DROP TABLE migrated_chats')
        answer = invoke(lab,inputs,from_database,database,names)
        if answer.returncode != 3 or any(rows(lab,database).values()):
            raise ValueError(f'The missing-{missing} migration must exit 3 and leave no destination row.')
        unchanged(before,rows(lab,source))
        if target_counter is not None and counter(lab.server,database) != target_counter:
            raise ValueError('A failed migration changed the target Draft counter.')
    second,second_opened = success()
    if normalized(first,opened) != normalized(second,second_opened):
        raise ValueError('A fresh repeated migration differs beyond the snapshot times.')
    report = {'check':'migration','root':inputs.root,'olderRoot':older.root,'sourceUnchanged':True,
            'unchangedTables':len(before),'sourceRows':sum(map(len,before.values())),
            'interruptedExchanges':len(opened),'provenanceRows':len(before['public.chats']),
            'missingSourceStatus':3,'missingTableStatus':3,'repeatable':True}
    if source_counter is not None:
        report['backendTables'] = {'exact':True,'sourceCounterUnchanged':True,'savedNextRevisions':revisions}
    return report


def check_migration(inputs: BuildInput, *, home: Path | None = None) -> dict[str,Any]:
    if inputs.older is None:
        return {'check':'migration','root':inputs.root,'olderRoot':None,'serverNeeded':False}
    older = origin(inputs,home or Path.home())
    script = inputs.file('migrate.sql').read_text(encoding='utf-8')
    protocol(script)
    for mode in inputs.modes:
        mode_protocol(script,mode)
    with private_server() as lab:
        report = run_migration(inputs,lab,older)
        if inputs.modes:
            report['optionalModes'] = check_modes(inputs,lab)
        return report


def main() -> int:
    try:
        verify(ROOT)
        report = check_migration(BuildInput.read(ROOT))
        verify(ROOT)
        print(json.dumps(report))
        return 0
    except (OSError,ValueError,RuntimeError,KeyError,SqlError,subprocess.SubprocessError) as error:
        print(f'migration check failed: {error}',file=sys.stderr)
        return 1


if __name__ == '__main__':
    raise SystemExit(main())

# Archived complete imports; restore needed names in their original scope, not at this file tail.
