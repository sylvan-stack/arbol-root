"""Compare a current Root layout with the latest qualified earlier files."""

from __future__ import annotations

import os
import uuid
from pathlib import Path
from typing import Any

from rct_conformance.tables import Catalog, catalog

from arbol_root.model import BUILD_ID, build_record
from scripts.sql_statements import preserves
from scripts.sql_support import BuildInput, SqlLab, regular

TABLES = """
SELECT format('%I.%I',n.nspname,c.relname) AS table
FROM pg_class c JOIN pg_namespace n ON n.oid=c.relnamespace
WHERE c.relkind IN ('r','p') AND n.nspname NOT LIKE 'pg_%' AND n.nspname<>'information_schema'
ORDER BY 1
"""
COLUMNS = """
SELECT format('%I.%I',n.nspname,c.relname) AS table, a.attname AS column,
       a.attnotnull AS required, d.oid IS NOT NULL AS has_default
FROM pg_class c JOIN pg_namespace n ON n.oid=c.relnamespace
JOIN pg_attribute a ON a.attrelid=c.oid AND a.attnum>0 AND NOT a.attisdropped
LEFT JOIN pg_attrdef d ON d.adrelid=c.oid AND d.adnum=a.attnum
WHERE c.relkind IN ('r','p') AND n.nspname NOT LIKE 'pg_%' AND n.nspname<>'information_schema'
ORDER BY 1,2
"""
CONSTRAINTS = """
SELECT format('%I.%I',n.nspname,c.relname) AS table, r.conname AS name,
       pg_get_constraintdef(r.oid) AS definition
FROM pg_constraint r JOIN pg_class c ON c.oid=r.conrelid
JOIN pg_namespace n ON n.oid=c.relnamespace
WHERE n.nspname NOT LIKE 'pg_%' AND n.nspname<>'information_schema'
ORDER BY 1,2
"""
INDEXES = """
SELECT format('%I.%I',n.nspname,c.relname) AS table,
       pg_get_indexdef(i.indexrelid) AS definition, i.indisunique AS unique
FROM pg_index i JOIN pg_class c ON c.oid=i.indrelid
JOIN pg_namespace n ON n.oid=c.relnamespace
WHERE n.nspname NOT LIKE 'pg_%' AND n.nspname<>'information_schema'
ORDER BY 1,2
"""
type Profile = dict[str, list[dict[str, Any]]]


def earlier_build(inputs: BuildInput) -> Path | None:
    with os.scandir(inputs.folder.parent) as entries:
        names = sorted(((int(entry.name,16),entry.name) for entry in entries
                        if BUILD_ID.fullmatch(entry.name) and entry.is_dir(follow_symlinks=False)
                        and int(entry.name,16) < int(inputs.number,16)), reverse=True)
    for _number, name in names:
        folder = inputs.folder.parent / name
        try:
            regular(folder / 'build.json')
            regular(folder / 'package.json')
            record = build_record(folder)
            if (record['root'] != inputs.root or record['build'] != name or record.get('status') != 'working'
                    or 'prunedAt' in record):
                continue
            for file in ['chat-tables.sql','root-tables.sql']:
                regular(folder / 'layout' / file)
            return folder
        except (OSError, ValueError, KeyError):
            continue
    return None


def profile(lab: SqlLab, database: str) -> Profile:
    return {name:lab.server.rows(database,query) for name,query in
            [('tables',TABLES),('columns',COLUMNS),('constraints',CONSTRAINTS),('indexes',INDEXES)]}


def additions(old: Catalog, new: Catalog, before: Profile, after: Profile) -> None:
    for kind, values in old.items():
        removed = set(values)-set(new.get(kind,[]))
        if removed:
            raise ValueError(f'The newer Build removed or changed older {kind}: {sorted(removed)}')
    for kind in ['schemas','triggers','functions','types','rules','policies','extensions','event triggers']:
        if new.get(kind,[]) != old.get(kind,[]):
            raise ValueError(f'Adding {kind} is outside the permitted table/column/index additions.')
    old_tables = {row['table'] for row in before['tables']}
    old_columns = {(row['table'],row['column']) for row in before['columns']}
    for row in after['columns']:
        if (row['table'] in old_tables and (row['table'],row['column']) not in old_columns
                and row['required'] and not row['has_default']):
            raise ValueError(f"An older table gained a NOT NULL column without a default: {row['table']}.{row['column']}")
    old_constraints = {(r['table'],r['name'],r['definition']) for r in before['constraints']}
    for row in after['constraints']:
        if row['table'] in old_tables and (row['table'],row['name'],row['definition']) not in old_constraints:
            raise ValueError(f"An older table gained a constraint: {row['table']}.{row['name']}")
    old_indexes = {row['definition'] for row in before['indexes']}
    for row in after['indexes']:
        if row['table'] in old_tables and row['definition'] not in old_indexes and row['unique']:
            raise ValueError(f"An older table gained a unique index: {row['definition']}")


def check_previous(inputs: BuildInput, lab: SqlLab, fresh: str) -> str | None:
    previous = earlier_build(inputs)
    if previous is None:
        return None
    for name in ['chat-tables.sql','root-tables.sql']:
        preserves((previous / 'layout' / name).read_text(encoding='utf-8'),
                  inputs.file(name).read_text(encoding='utf-8'))
    combined = 'combined_'+uuid.uuid4().hex
    lab.server.createdb(combined)
    for name in ['chat-tables.sql','root-tables.sql']:
        lab.run_file(combined, previous / 'layout' / name)
    old, before = catalog(lab.server,combined), profile(lab,combined)
    for name in ['chat-tables.sql','root-tables.sql']:
        lab.run_file(combined, inputs.file(name))
    additions(old,catalog(lab.server,combined),before,profile(lab,combined))
    if lab.dump(combined) != lab.dump(fresh):
        raise ValueError('Earlier-then-current and fresh-current pg_dump schemas differ.')
    return previous.name
