"""Fictional BKD rows and counter checks for Root-owned SQL qualification."""

from __future__ import annotations

import json
import uuid
from decimal import Decimal
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from rct_conformance.postgres import Server

TABLES = ("drafts", "chat_settings", "chat_marks", "exchange_notes")
COUNTER = "drafts_revision"
DRAFTS = [f"30000000-0000-4000-8000-{n:012d}" for n in range(1, 4)]


def rows(server: Server, database: str) -> dict[str, list[dict[str, Any]]]:
    """Keep numeric JSON exact instead of comparing rounded Python floats."""
    return {
        table: [
            json.loads(row["value"], parse_float=Decimal)
            for row in server.rows(
                database, f"SELECT row_to_json(t)::text AS value FROM {table} t ORDER BY row_to_json(t)::text"
            )
        ]
        for table in TABLES
    }


def present(server: Server, database: str) -> bool:
    names = (*TABLES, COUNTER)
    value = server.value(
        database,
        "SELECT json_build_array(" + ",".join("to_regclass('public." + name + "') IS NOT NULL" for name in names) + ")",
    )
    if any(value) and not all(value):
        raise ValueError("The backend qualification fixture has a partial layout.")
    return bool(all(value))


def counter(server: Server, database: str) -> dict[str, Any]:
    value = server.value(database, "SELECT json_build_object('last_value',last_value,'log_cnt',log_cnt,"
                         "'is_called',is_called) FROM drafts_revision")
    if not isinstance(value, dict):
        raise ValueError("The Draft counter returned no row.")
    return value


def seed(server: Server, database: str, chats: list[str], exchanges: list[str], special: str) -> None:
    if not present(server, database):
        return

    # Hex-encoded text avoids any SQL/client interpretation of the fictional CRLF/backslash text.
    def text(value: str) -> str:
        return "convert_from(decode('" + value.encode("utf-8").hex() + "','hex'),'UTF8')"

    request = (
        '{"chat":"' + chats[1] + '","workingFolder":"/fictional/readonly","extra":0.123456789012345678901234567890}'
    )
    server.execute(
        database,
        f"""
INSERT INTO drafts VALUES
 ('{DRAFTS[0]}','{chats[0]}',NULL,{text("open chat " + special)},41,NULL,NULL,'2026-10-27T06:00:00Z'),
 ('{DRAFTS[1]}','{chats[1]}',NULL,{text("pending chat " + special)},67,'50000000-0000-4000-8000-000000000001',{text(request)}::jsonb,'2026-10-27T06:01:00Z'),
 ('{DRAFTS[2]}',NULL,'/fictional/repository',{text("repository " + special)},90,NULL,NULL,'2026-10-27T06:02:00Z');
INSERT INTO chat_settings VALUES
 ('{chats[0]}','{{"driver":"fictional","model":"one","exact":0.123456789012345678901234567890}}','/fictional/first','2026-10-27T06:00:00Z'),
 ('{chats[1]}',NULL,NULL,'2026-10-27T06:00:00Z');
INSERT INTO chat_marks VALUES
 ('{chats[0]}',true,NULL,'2026-10-27T06:00:00Z'),
 ('{chats[1]}',false,'2026-10-27T06:03:00Z','2026-10-27T06:03:00Z');
INSERT INTO exchange_notes VALUES
 ('{exchanges[0]}','ended_stuck','2026-10-27T06:00:00Z'),
 ('{exchanges[3]}','ended_stuck','2026-10-27T06:00:00Z');
SELECT setval('drafts_revision',100,true);
""",
    )


def next_draft(server: Server, database: str, source_counter: dict[str, Any], maximum: int) -> int:
    """Actually save/remove a new repository Draft; a deleted consumed revision still cannot be reused."""
    draft = str(uuid.uuid4())
    value = server.value(
        database,
        f"""WITH saved AS (
 INSERT INTO drafts VALUES ('{draft}',NULL,'/fictional/new-{draft}','after migration',
 nextval('drafts_revision'),NULL,NULL,clock_timestamp()) RETURNING revision)
 SELECT to_json(revision) FROM saved""",
    )
    if (
        type(value) is not int
        or value <= maximum
        or value < source_counter["last_value"] + int(source_counter["is_called"])
    ):
        raise ValueError("The migrated Draft reused a saved or consumed revision.")
    server.execute(database, f"DELETE FROM drafts WHERE id='{draft}'")
    return value
