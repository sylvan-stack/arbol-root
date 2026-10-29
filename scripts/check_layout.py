# Test implementations moved to tests/mid/archived/scripts/check_layout.py.
"""Qualify the numbered Build's two layouts on a server of this check's own."""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / 'src'))
sys.path.insert(0, str(ROOT / 'contract/conformance'))

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
    raise RuntimeError('Tests are commented under the tier policy; see TESTS.md. Restore only in an explicitly requested testing task.')  # TEST-TIER-REFUSAL


def main() -> int:
    raise RuntimeError('Tests are commented under the tier policy; see TESTS.md. Restore only in an explicitly requested testing task.')  # TEST-TIER-REFUSAL


if __name__ == '__main__':
    raise SystemExit(main())

# Archived complete imports; restore needed names in their original scope, not at this file tail.
