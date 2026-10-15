"""What the database's layout is, and R16: no table changed (RCT-4, RCT-3.1).

The layout is read from PostgreSQL's catalogue: every schema, relation, column, check and key, index, trigger,
function, type, rule, policy, comment and extension outside PostgreSQL's own schemas. The suite reads it right after
`layout.sql` has made the scenario's database, before any Trunk starts, and again after the scenario; R16 passes
when the two are the same and every row belongs to an Exchange the scenario ran.
"""

from __future__ import annotations

from collections.abc import Iterable
from typing import Any

from .judge import Mismatch
from .postgres import Server

_USER = ("SELECT oid, nspname FROM pg_namespace WHERE nspname NOT IN ('pg_catalog', 'information_schema', 'pg_toast')"
         " AND nspname NOT LIKE 'pg_temp_%' AND nspname NOT LIKE 'pg_toast_temp_%'")

_KINDS: dict[str, str] = {
    "schemas": "SELECT nspname AS x FROM ns",
    "relations": "SELECT format('%s.%s (kind %s)', n.nspname, c.relname, c.relkind) AS x"
                 " FROM pg_class c JOIN ns n ON n.oid = c.relnamespace",
    "columns": "SELECT format('%s.%s.%s %s not null %s default %s identity %s generated %s', n.nspname, c.relname,"
               " a.attname, format_type(a.atttypid, a.atttypmod), a.attnotnull, pg_get_expr(d.adbin, d.adrelid),"
               " a.attidentity, a.attgenerated) AS x"
               " FROM pg_attribute a JOIN pg_class c ON c.oid = a.attrelid JOIN ns n ON n.oid = c.relnamespace"
               " LEFT JOIN pg_attrdef d ON d.adrelid = a.attrelid AND d.adnum = a.attnum"
               " WHERE a.attnum > 0 AND NOT a.attisdropped",
    "constraints": "SELECT format('%s %s %s', CASE WHEN r.conrelid <> 0 THEN r.conrelid::regclass::text ELSE t.typname END, r.conname,"
                   " pg_get_constraintdef(r.oid)) AS x FROM pg_constraint r JOIN ns n ON n.oid = r.connamespace"
                   " LEFT JOIN pg_type t ON t.oid = r.contypid",
    "indexes": "SELECT pg_get_indexdef(i.indexrelid) AS x FROM pg_index i JOIN pg_class c ON c.oid = i.indrelid"
               " JOIN ns n ON n.oid = c.relnamespace",
    "triggers": "SELECT pg_get_triggerdef(t.oid) AS x FROM pg_trigger t JOIN pg_class c ON c.oid = t.tgrelid"
                " JOIN ns n ON n.oid = c.relnamespace WHERE NOT t.tgisinternal",
    "functions": "SELECT format('%s.%s(%s) (kind %s)', n.nspname, p.proname, pg_get_function_identity_arguments(p.oid),"
                 " p.prokind) AS x FROM pg_proc p JOIN ns n ON n.oid = p.pronamespace",
    "types": "SELECT format('%s.%s (type %s)', n.nspname, t.typname, t.typtype) AS x FROM pg_type t"
             " JOIN ns n ON n.oid = t.typnamespace WHERE t.typrelid = 0 AND t.typcategory <> 'A'",
    "rules": "SELECT format('%s.%s %s', r.schemaname, r.tablename, r.definition) AS x FROM pg_rules r"
             " WHERE r.schemaname IN (SELECT nspname FROM ns)",
    "policies": "SELECT format('%s.%s %s %s %s', p.schemaname, p.tablename, p.policyname, p.cmd, p.qual) AS x"
                " FROM pg_policies p WHERE p.schemaname IN (SELECT nspname FROM ns)",
    "comments": "SELECT format('%s.%s%s: %s', n.nspname, c.relname, coalesce('.' || a.attname, ''), d.description) AS x"
                " FROM pg_description d JOIN pg_class c ON d.classoid = 'pg_class'::regclass AND c.oid = d.objoid"
                " JOIN ns n ON n.oid = c.relnamespace"
                " LEFT JOIN pg_attribute a ON a.attrelid = c.oid AND a.attnum = d.objsubid AND d.objsubid > 0",
    "extensions": "SELECT extname AS x FROM pg_extension",
    "event triggers": "SELECT evtname AS x FROM pg_event_trigger",
}

CATALOG = (f"WITH ns AS ({_USER}) SELECT json_build_object(" + ", ".join(
    f"'{kind}', (SELECT coalesce(json_agg(s.x ORDER BY s.x), '[]'::json) FROM ({query}) s)"
    for kind, query in _KINDS.items()) + ")")

Catalog = dict[str, list[str]]


def catalog(server: Server, database: str) -> Catalog:
    """The layout of a database, kind by kind, each a sorted list of lines."""
    value = server.value(database, CATALOG)
    assert isinstance(value, dict)
    return {kind: [str(item) for item in items] for kind, items in value.items()}


def differences(before: Catalog, after: Catalog) -> list[str]:
    """What `after` adds to or lacks of `before`, one line each, such as "added indexes: CREATE INDEX …"."""
    lines: list[str] = []
    for kind in sorted(set(before) | set(after)):
        old, new = set(before.get(kind, [])), set(after.get(kind, []))
        lines += [f"added {kind}: {item}" for item in sorted(new - old)]
        lines += [f"removed {kind}: {item}" for item in sorted(old - new)]
    return lines


ROWS = ("SELECT json_build_object("
        "'chats', (SELECT coalesce(json_agg(id::text ORDER BY id), '[]'::json) FROM chats), "
        "'exchanges', (SELECT coalesce(json_agg(json_build_object('id', id::text, 'chat', chat_id::text) ORDER BY id),"
        " '[]'::json) FROM exchanges), "
        "'messages', (SELECT coalesce(json_agg(DISTINCT exchange_id::text), '[]'::json) FROM messages), "
        "'tool_calls', (SELECT coalesce(json_agg(DISTINCT exchange_id::text), '[]'::json) FROM tool_calls), "
        "'runs', (SELECT coalesce(json_agg(DISTINCT exchange_id::text), '[]'::json) FROM runs))")


def no_table_changed(server: Server, database: str, layout: Catalog, exchanges: Iterable[str],
                     chats: Iterable[str]) -> None:
    """R16: the database's layout is the one `layout.sql` made, and no row belongs to an Exchange the scenario did not
    run. `exchanges` and `chats` are those of the scenario's acceptances."""
    changed = differences(layout, catalog(server, database))
    if changed:
        raise Mismatch("R16: the tables are not those layout.sql made:\n    " + "\n    ".join(changed))
    rows: Any = server.value(database, ROWS)
    known = set(exchanges)
    known_chats = set(chats) | {row["chat"] for row in rows["exchanges"] if row["id"] in known}
    foreign: list[str] = []
    foreign += [f"exchanges: {row['id']}" for row in rows["exchanges"] if row["id"] not in known]
    for table in ("messages", "tool_calls", "runs"):
        foreign += [f"{table}: rows of Exchange {exchange}" for exchange in rows[table] if exchange not in known]
    foreign += [f"chats: {chat}" for chat in rows["chats"] if chat not in known_chats]
    if foreign:
        raise Mismatch("R16: rows that belong to no Exchange the scenario ran:\n    " + "\n    ".join(foreign))
