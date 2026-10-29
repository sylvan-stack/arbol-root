# Test implementations moved to tests/mid/archived/contract/conformance/tests/test_layout.py.
"""The layout of Root Contract version 1, `contract/1/layout.sql` (RCT-3.6), on a server of the test's own.

The file is the whole of RCT-3's Interface; it runs twice and the second run changes nothing; every table and column
has a comment; and the refusals recorded in RCT-3 on 15 October 2026 happen.
"""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from rct_conformance.postgres import Server, SqlError

from .support import LAYOUT

TABLES = ("chats", "exchanges", "messages", "tool_calls", "runs")
CHAT = "c3d4e5f6-0718-4293-a4b5-c6d7e8f90a1b"
EXCHANGE = "7f3a2c1e-4b5d-4e6f-8a9b-0c1d2e3f4a5b"


def chat(chat_id: str = CHAT) -> str:
    return f"INSERT INTO chats (id, created_at) VALUES ('{chat_id}', now());"


def exchange(exchange_id: str = EXCHANGE, *, number: int = 1, state: str = "open", error: str | None = None,
             chat_id: str = CHAT, replaced_by: str | None = None) -> str:
    ended = "NULL" if state == "open" else "now()"
    cause = "NULL" if error is None else f"'{error}'"
    replaced = "NULL" if replaced_by is None else f"'{replaced_by}'"
    return ("INSERT INTO exchanges (id, chat_id, number, state, error, trunk, build, route, working_folder,"
            " accepted_at, ended_at, replaced_by) VALUES"
            f" ('{exchange_id}', '{chat_id}', {number}, '{state}', {cause}, 'trivial', '4',"
            f" '{{\"driver\": \"claude\"}}', '/Users/sam/repos/shop', now(), {ended}, {replaced});")


class Layout(unittest.TestCase):
    server: Server
    folder: tempfile.TemporaryDirectory[str]
    databases = 0

    @classmethod
    def setUpClass(cls) -> None:
        cls.folder = tempfile.TemporaryDirectory(prefix="rct-layout-")
        cls.server = Server.create(Path(cls.folder.name) / "postgres")

    @classmethod
    def tearDownClass(cls) -> None:
        cls.server.remove()
        cls.folder.cleanup()

    def database(self) -> str:
        """A new database of the test's server, with the layout run once."""
        type(self).databases += 1
        name = f"layout_{type(self).databases}"
        self.server.createdb(name)
        self.server.run_file(name, LAYOUT)
        return name

    def refused(self, database: str, sql: str) -> SqlError:
        """The error of statements that one transaction runs and the server refuses; nothing of them stays."""
        with self.assertRaises(SqlError) as refusal:
            self.server.execute(database, sql)
        return refusal.exception












if __name__ == "__main__":
    unittest.main()

# Archived complete imports; restore needed names in their original scope, not at this file tail.
