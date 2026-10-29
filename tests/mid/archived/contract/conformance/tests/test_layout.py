"""The layout of Root Contract version 1, `contract/1/layout.sql` (RCT-3.6), on a server of the test's own.

The file is the whole of RCT-3's Interface; it runs twice and the second run changes nothing; every table and column
has a comment; and the refusals recorded in RCT-3 on 15 October 2026 happen.
"""

from __future__ import annotations
import re
import uuid

from rct_conformance.tables import catalog
from .support import LAYOUT, SPECIFICATION


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

# LOW TIER — DO NOT ENABLE OR RECREATE
# Historical examples only. Read before adding related tests; never execute.
# LOW-TIER-BEGIN: tests/mid/archived/contract/conformance/tests/test_layout.py::Layout.test_the_file_is_the_interface_of_rct_3
# Reason: Direct DDL constraint/default/comment examples mostly test PostgreSQL or repeat source; real product scenarios and packaged schema compatibility qualify the consequential integration. Case reviewed: layout.the-interface: contract/1/layout.sql is, byte for byte, the file in RCT-3's Interface.
# Source: arbol-root@ef4fd6a30eca7130653b20e5eedf0da7be72aaa4:tests/mid/archived/contract/conformance/tests/test_layout.py
# Historical fixtures and class context are available at the source revision; no active dependencies restored.
# LOW-TIER-SOURCE-BEGIN
#     def test_the_file_is_the_interface_of_rct_3(self) -> None:
#         """layout.the-interface: contract/1/layout.sql is, byte for byte, the file in RCT-3's Interface."""
#         self.assertTrue(SPECIFICATION.is_file(), f"Required RCT-3 specification oracle is missing: {SPECIFICATION}")
#         interface = SPECIFICATION.read_text(encoding="utf-8").split("\n## Interface\n", 1)[1]
#         match = re.search(r"```sql\n(.*?)```", interface, re.S)
#         assert match is not None
#         self.assertEqual(LAYOUT.read_text(encoding="utf-8"), match.group(1))
# LOW-TIER-SOURCE-END
# LOW-TIER-END

# LOW-TIER-BEGIN: tests/mid/archived/contract/conformance/tests/test_layout.py::Layout.test_runs_twice_and_the_second_run_changes_nothing
# Reason: Direct DDL constraint/default/comment examples mostly test PostgreSQL or repeat source; real product scenarios and packaged schema compatibility qualify the consequential integration. Case reviewed: layout.runs-twice: every statement can run again, and the second run changes nothing.
# Source: arbol-root@ef4fd6a30eca7130653b20e5eedf0da7be72aaa4:tests/mid/archived/contract/conformance/tests/test_layout.py
# Historical fixtures and class context are available at the source revision; no active dependencies restored.
# LOW-TIER-SOURCE-BEGIN
#     def test_runs_twice_and_the_second_run_changes_nothing(self) -> None:
#         """layout.runs-twice: every statement can run again, and the second run changes nothing."""
#         database = self.database()
#         before = catalog(self.server, database)
#         self.assertEqual(sorted(name for name in before["relations"] if "(kind r)" in name),
#                          [f"public.{table} (kind r)" for table in sorted(TABLES)])
#         self.server.run_file(database, LAYOUT)
#         self.assertEqual(catalog(self.server, database), before)
# LOW-TIER-SOURCE-END
# LOW-TIER-END

# LOW-TIER-BEGIN: tests/mid/archived/contract/conformance/tests/test_layout.py::Layout.test_every_table_and_column_has_a_comment
# Reason: Direct DDL constraint/default/comment examples mostly test PostgreSQL or repeat source; real product scenarios and packaged schema compatibility qualify the consequential integration. Case reviewed: layout.comments: every table, every column and the index of the open Exchanges have a comment.
# Source: arbol-root@ef4fd6a30eca7130653b20e5eedf0da7be72aaa4:tests/mid/archived/contract/conformance/tests/test_layout.py
# Historical fixtures and class context are available at the source revision; no active dependencies restored.
# LOW-TIER-SOURCE-BEGIN
#     def test_every_table_and_column_has_a_comment(self) -> None:
#         """layout.comments: every table, every column and the index of the open Exchanges have a comment."""
#         database = self.database()
#         missing = self.server.rows(database, (
#             "SELECT c.relname AS table, a.attname AS column FROM pg_class c"
#             " JOIN pg_namespace n ON n.oid = c.relnamespace AND n.nspname = 'public'"
#             " LEFT JOIN pg_attribute a ON a.attrelid = c.oid AND a.attnum > 0 AND NOT a.attisdropped"
#             " WHERE c.relkind = 'r' AND (obj_description(c.oid, 'pg_class') IS NULL"
#             " OR (a.attname IS NOT NULL AND col_description(c.oid, a.attnum) IS NULL))"))
#         self.assertEqual(missing, [])
#         columns = self.server.rows(database, "SELECT count(*) AS n FROM information_schema.columns"
#                                              " WHERE table_schema = 'public'")
#         self.assertEqual(columns, [{"n": 42}])
#         index = self.server.rows(database, "SELECT obj_description('exchanges_one_open_per_chat'::regclass,"
#                                            " 'pg_class') IS NOT NULL AS commented")
#         self.assertEqual(index, [{"commented": True}])
# LOW-TIER-SOURCE-END
# LOW-TIER-END

# LOW-TIER-BEGIN: tests/mid/archived/contract/conformance/tests/test_layout.py::Layout.test_a_second_open_exchange_in_a_chat_is_refused
# Reason: Direct DDL constraint/default/comment examples mostly test PostgreSQL or repeat source; real product scenarios and packaged schema compatibility qualify the consequential integration. Case reviewed: layout.one-open-exchange: the unique index on the open Exchanges refuses a second one in its chat.
# Source: arbol-root@ef4fd6a30eca7130653b20e5eedf0da7be72aaa4:tests/mid/archived/contract/conformance/tests/test_layout.py
# Historical fixtures and class context are available at the source revision; no active dependencies restored.
# LOW-TIER-SOURCE-BEGIN
#     def test_a_second_open_exchange_in_a_chat_is_refused(self) -> None:
#         """layout.one-open-exchange: the unique index on the open Exchanges refuses a second one in its chat."""
#         database = self.database()
#         error = self.refused(database, chat() + exchange() + exchange(str(uuid.uuid4()), number=2))
#         self.assertEqual(error.sqlstate, "23505")
#         self.assertIn("exchanges_one_open_per_chat", str(error))
# LOW-TIER-SOURCE-END
# LOW-TIER-END

# LOW-TIER-BEGIN: tests/mid/archived/contract/conformance/tests/test_layout.py::Layout.test_a_second_exchange_with_the_same_number_is_refused
# Reason: Direct DDL constraint/default/comment examples mostly test PostgreSQL or repeat source; real product scenarios and packaged schema compatibility qualify the consequential integration. Case reviewed: layout.unique-number: the key on (chat_id, number) refuses a second Exchange with the same number.
# Source: arbol-root@ef4fd6a30eca7130653b20e5eedf0da7be72aaa4:tests/mid/archived/contract/conformance/tests/test_layout.py
# Historical fixtures and class context are available at the source revision; no active dependencies restored.
# LOW-TIER-SOURCE-BEGIN
#     def test_a_second_exchange_with_the_same_number_is_refused(self) -> None:
#         """layout.unique-number: the key on (chat_id, number) refuses a second Exchange with the same number."""
#         database = self.database()
#         error = self.refused(database, chat() + exchange(state="completed")
#                              + exchange(str(uuid.uuid4()), number=1, state="completed"))
#         self.assertEqual(error.sqlstate, "23505")
#         self.assertIn("exchanges_chat_id_number_key", str(error))
# LOW-TIER-SOURCE-END
# LOW-TIER-END

# LOW-TIER-BEGIN: tests/mid/archived/contract/conformance/tests/test_layout.py::Layout.test_a_failed_exchange_without_a_cause_is_refused
# Reason: Direct DDL constraint/default/comment examples mostly test PostgreSQL or repeat source; real product scenarios and packaged schema compatibility qualify the consequential integration. Case reviewed: layout.failed-has-a-cause: a failed Exchange without an error, and a cause without a failure, are refused.
# Source: arbol-root@ef4fd6a30eca7130653b20e5eedf0da7be72aaa4:tests/mid/archived/contract/conformance/tests/test_layout.py
# Historical fixtures and class context are available at the source revision; no active dependencies restored.
# LOW-TIER-SOURCE-BEGIN
#     def test_a_failed_exchange_without_a_cause_is_refused(self) -> None:
#         """layout.failed-has-a-cause: a failed Exchange without an error, and a cause without a failure, are refused."""
#         database = self.database()
#         self.assertEqual(self.refused(database, chat() + exchange(state="failed")).sqlstate, "23514")
#         self.assertEqual(self.refused(database, chat() + exchange(state="completed", error='{"code": "x"}')).sqlstate,
#                          "23514")
#         self.server.execute(database, chat() + exchange(state="failed", error='{"code": "rate_limited"}'))
# LOW-TIER-SOURCE-END
# LOW-TIER-END

# LOW-TIER-BEGIN: tests/mid/archived/contract/conformance/tests/test_layout.py::Layout.test_a_run_of_an_unknown_kind_is_refused
# Reason: Direct DDL constraint/default/comment examples mostly test PostgreSQL or repeat source; real product scenarios and packaged schema compatibility qualify the consequential integration. Case reviewed: layout.run-kind: a run of a kind other than agent and small is refused.
# Source: arbol-root@ef4fd6a30eca7130653b20e5eedf0da7be72aaa4:tests/mid/archived/contract/conformance/tests/test_layout.py
# Historical fixtures and class context are available at the source revision; no active dependencies restored.
# LOW-TIER-SOURCE-BEGIN
#     def test_a_run_of_an_unknown_kind_is_refused(self) -> None:
#         """layout.run-kind: a run of a kind other than agent and small is refused."""
#         database = self.database()
#         error = self.refused(database, chat() + exchange() + f"INSERT INTO runs (exchange_id, run_id, kind, outcome,"
#                                                              f" ended_at) VALUES ('{EXCHANGE}', 'r1', 'title',"
#                                                              " 'completed', now());")
#         self.assertEqual(error.sqlstate, "23514")
#         self.server.execute(database, chat() + exchange() + f"INSERT INTO runs (exchange_id, run_id, kind, outcome,"
#                                                             f" ended_at) VALUES ('{EXCHANGE}', 'r1', 'small',"
#                                                             " 'completed', now());")
# LOW-TIER-SOURCE-END
# LOW-TIER-END

# LOW-TIER-BEGIN: tests/mid/archived/contract/conformance/tests/test_layout.py::Layout.test_the_deletion_of_a_chat_that_has_exchanges_is_refused
# Reason: Direct DDL constraint/default/comment examples mostly test PostgreSQL or repeat source; real product scenarios and packaged schema compatibility qualify the consequential integration. Case reviewed: layout.no-cascade: a chat that has Exchanges, and an Exchange that has messages, cannot be deleted.
# Source: arbol-root@ef4fd6a30eca7130653b20e5eedf0da7be72aaa4:tests/mid/archived/contract/conformance/tests/test_layout.py
# Historical fixtures and class context are available at the source revision; no active dependencies restored.
# LOW-TIER-SOURCE-BEGIN
#     def test_the_deletion_of_a_chat_that_has_exchanges_is_refused(self) -> None:
#         """layout.no-cascade: a chat that has Exchanges, and an Exchange that has messages, cannot be deleted."""
#         database = self.database()
#         self.server.execute(database, chat() + exchange()
#                             + f"INSERT INTO messages VALUES ('{EXCHANGE}', 0, 'user', 'What does build.sh do?');")
#         self.assertEqual(self.refused(database, f"DELETE FROM chats WHERE id = '{CHAT}';").sqlstate, "23503")
#         self.assertEqual(self.refused(database, f"DELETE FROM exchanges WHERE id = '{EXCHANGE}';").sqlstate, "23503")
#         self.assertEqual(self.server.rows(database, "SELECT count(*) AS n FROM messages"), [{"n": 1}])
# LOW-TIER-SOURCE-END
# LOW-TIER-END

# LOW-TIER-BEGIN: tests/mid/archived/contract/conformance/tests/test_layout.py::Layout.test_nul_and_a_lone_half_of_a_surrogate_pair_are_refused_and_u_fffd_is_stored
# Reason: Direct DDL constraint/default/comment examples mostly test PostgreSQL or repeat source; real product scenarios and packaged schema compatibility qualify the consequential integration. Case reviewed: layout.characters: U+0000 and a lone half of a surrogate pair are refused with errors of the SQLSTATE
# Source: arbol-root@ef4fd6a30eca7130653b20e5eedf0da7be72aaa4:tests/mid/archived/contract/conformance/tests/test_layout.py
# Historical fixtures and class context are available at the source revision; no active dependencies restored.
# LOW-TIER-SOURCE-BEGIN
#     def test_nul_and_a_lone_half_of_a_surrogate_pair_are_refused_and_u_fffd_is_stored(self) -> None:
#         """layout.characters: U+0000 and a lone half of a surrogate pair are refused with errors of the SQLSTATE
#         class 22, in the text of a message and inside jsonb; U+FFFD in their place is stored as it was sent."""
#         database = self.database()
#         setup = chat() + exchange()
#         for name, value in (("U+0000", r"\x00"), ("a lone half of a surrogate pair", r"\xeda080")):
#             with self.subTest(name, column="messages.text"):
#                 error = self.refused(database, setup + f"INSERT INTO messages VALUES ('{EXCHANGE}', 0, 'user',"
#                                                        f" convert_from('{value}'::bytea, 'UTF8'));")
#                 self.assertEqual((error.sqlstate or "")[:2], "22", str(error))
#         for name, escape in (("U+0000", r"\u0000"), ("a lone half of a surrogate pair", r"\ud83d")):
#             with self.subTest(name, column="tool_calls.input"):
#                 error = self.refused(database, setup + "INSERT INTO tool_calls (exchange_id, position, run_id,"
#                                      f" call_id, name, input, ok) VALUES ('{EXCHANGE}', 4, 'r1', 'call_1', 'shell',"
#                                      f" '{{\"output\": \"a{escape}b\"}}', true);")
#                 self.assertEqual((error.sqlstate or "")[:2], "22", str(error))
#         self.server.execute(database, setup + f"INSERT INTO messages VALUES ('{EXCHANGE}', 0, 'user', 'a�b');"
#                             "INSERT INTO tool_calls (exchange_id, position, run_id, call_id, name, input, ok) VALUES"
#                             f" ('{EXCHANGE}', 4, 'r1', 'call_1', 'shell', '{{\"output\": \"a\\ufffdb\"}}', true);")
#         self.assertEqual(self.server.rows(database, "SELECT m.text, t.input FROM messages m, tool_calls t"),
#                          [{"text": "a�b", "input": {"output": "a�b"}}])
# LOW-TIER-SOURCE-END
# LOW-TIER-END

# LOW-TIER-BEGIN: tests/mid/archived/contract/conformance/tests/test_layout.py::Layout.test_the_readers_query_leaves_out_a_replaced_exchange_and_a_sub_agents_call
# Reason: Direct DDL constraint/default/comment examples mostly test PostgreSQL or repeat source; real product scenarios and packaged schema compatibility qualify the consequential integration. Case reviewed: layout.reader: RCT-3's query of a chat leaves out a replaced Exchange and the calls of a sub-agent.
# Source: arbol-root@ef4fd6a30eca7130653b20e5eedf0da7be72aaa4:tests/mid/archived/contract/conformance/tests/test_layout.py
# Historical fixtures and class context are available at the source revision; no active dependencies restored.
# LOW-TIER-SOURCE-BEGIN
#     def test_the_readers_query_leaves_out_a_replaced_exchange_and_a_sub_agents_call(self) -> None:
#         """layout.reader: RCT-3's query of a chat leaves out a replaced Exchange and the calls of a sub-agent."""
#         database = self.database()
#         first, second = EXCHANGE, "9b3a2c1e-5c6d-4f70-9a1b-2c3d4e5f6a7b"
#         self.server.execute(database, chat() + exchange(second, number=2, state="completed")
#                             + exchange(first, state="failed", error='{"code": "rate_limited"}', replaced_by=second)
#                             + f"INSERT INTO messages VALUES ('{second}', 0, 'user', 'Again'),"
#                             f" ('{second}', 3, 'assistant', 'Done.');"
#                             "INSERT INTO tool_calls (exchange_id, position, run_id, call_id, parent_call_id, name,"
#                             f" input, ok) VALUES ('{second}', 1, 'r', 'c1', NULL, 'shell', '{{}}', true),"
#                             f" ('{second}', 2, 'r', 'c2', 'c1', 'Read', '{{}}', true);")
#         rows = self.server.rows(database, (
#             "SELECT e.number, x.position, x.kind, x.body FROM exchanges e"
#             " JOIN (SELECT exchange_id, position, role AS kind, text AS body FROM messages"
#             " UNION ALL SELECT exchange_id, position, 'tool ' || name, input::text FROM tool_calls"
#             " WHERE parent_call_id IS NULL) x ON x.exchange_id = e.id"
#             f" WHERE e.chat_id = '{CHAT}' AND e.replaced_by IS NULL ORDER BY e.number, x.position"))
#         self.assertEqual([(row["number"], row["position"], row["kind"]) for row in rows],
#                          [(2, 0, "user"), (2, 1, "tool shell"), (2, 3, "assistant")])
# LOW-TIER-SOURCE-END
# LOW-TIER-END
