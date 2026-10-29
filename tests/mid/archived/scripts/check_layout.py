"""Qualify the numbered Build's two layouts on a server of this check's own."""

from __future__ import annotations
import json
import subprocess
import uuid


import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / 'src'))
sys.path.insert(0, str(ROOT / 'contract/conformance'))
from rct_conformance.postgres import SqlError  # noqa: E402
from rct_conformance.tables import catalog  # noqa: E402
from scripts.layout_compatibility import check_previous  # noqa: E402
from scripts.package_support import verify  # noqa: E402
from scripts.sql_statements import layout_statements  # noqa: E402
from scripts.sql_support import BuildInput, SqlLab, private_server  # noqa: E402


from scripts.sql_support import BuildInput, SqlLab  # noqa: E402

COMMENTS = """
SELECT n.nspname AS schema, c.relname AS table, a.attname AS column
FROM pg_class c JOIN pg_namespace n ON n.oid=c.relnamespace
LEFT JOIN pg_attribute a ON a.attrelid=c.oid AND a.attnum>0 AND NOT a.attisdropped
WHERE c.relkind IN ('r','p') AND n.nspname NOT LIKE 'pg_%' AND n.nspname<>'information_schema'
AND (coalesce(btrim(obj_description(c.oid,'pg_class')),'')=''
     OR (a.attname IS NOT NULL AND coalesce(btrim(col_description(c.oid,a.attnum)),'')=''))
ORDER BY n.nspname,c.relname,a.attnum
"""
SEQUENCE_COMMENTS = """
SELECT n.nspname AS schema, c.relname AS sequence
FROM pg_class c JOIN pg_namespace n ON n.oid=c.relnamespace
WHERE c.relkind='S' AND n.nspname NOT LIKE 'pg_%' AND n.nspname<>'information_schema'
AND coalesce(btrim(obj_description(c.oid,'pg_class')),'')=''
ORDER BY 1,2
"""


def run_layout(inputs: BuildInput, lab: SqlLab) -> dict[str, Any]:
    files = [inputs.file(name) for name in ['chat-tables.sql', 'root-tables.sql']]
    for file in files:
        layout_statements(file.read_text(encoding='utf-8'))
    database = 'layout_'+uuid.uuid4().hex
    lab.server.createdb(database)
    for file in files:
        lab.run_file(database, file)
    missing = lab.server.rows(database, COMMENTS)
    if missing:
        raise ValueError(f'Every table and column needs a nonempty comment: {missing}')
    missing_sequences = lab.server.rows(database, SEQUENCE_COMMENTS)
    if missing_sequences:
        raise ValueError(f'Every sequence needs a nonempty comment: {missing_sequences}')
    before = catalog(lab.server, database)
    dumped = lab.dump(database)
    for file in files:
        lab.run_file(database, file)
    if catalog(lab.server, database) != before or lab.dump(database) != dumped:
        raise ValueError('Repeating the two layouts changed the schema.')
    previous = check_previous(inputs, lab, database)
    return {'check':'layout', 'root':inputs.root, 'repeated':True, 'earlierBuild':previous}


def main() -> int:
    try:
        verify(ROOT)
        inputs = BuildInput.read(ROOT)
        with private_server() as lab:
            report = run_layout(inputs, lab)
        verify(ROOT)
        print(json.dumps(report))
        return 0
    except (OSError, ValueError, RuntimeError, KeyError, SqlError, subprocess.SubprocessError) as error:
        print(f'layout check failed: {error}', file=sys.stderr)
        return 1


if __name__ == '__main__':
    raise SystemExit(main())

# Archived complete imports; restore needed names in their original scope, not at this file tail.
