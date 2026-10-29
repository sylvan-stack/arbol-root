# Test implementations moved to tests/mid/archived/scripts/check_migration.py.
"""Qualify copied migration SQL with fictional history on one disposable server."""

from __future__ import annotations

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
    raise RuntimeError('Tests are commented under the tier policy; see TESTS.md. Restore only in an explicitly requested testing task.')  # TEST-TIER-REFUSAL


def check_migration(inputs: BuildInput, *, home: Path | None = None) -> dict[str,Any]:
    raise RuntimeError('Tests are commented under the tier policy; see TESTS.md. Restore only in an explicitly requested testing task.')  # TEST-TIER-REFUSAL


def main() -> int:
    raise RuntimeError('Tests are commented under the tier policy; see TESTS.md. Restore only in an explicitly requested testing task.')  # TEST-TIER-REFUSAL


if __name__ == '__main__':
    raise SystemExit(main())

# Archived complete imports; restore needed names in their original scope, not at this file tail.
