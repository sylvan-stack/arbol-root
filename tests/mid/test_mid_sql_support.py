"""Mid-tier selections. Write or run only in an explicitly requested testing task."""
from __future__ import annotations

import test_sql_support as _support
from test_sql_support import (ROOT ,mock ,os ,private_server)


class SqlSupport(_support.SqlSupport):


# TEST-TIER-BEGIN tests/test_sql_support.py::SqlSupport.test_private_server_ignores_caller_pg_variables_and_dumps_a_stable_schema
    def test_private_server_ignores_caller_pg_variables_and_dumps_a_stable_schema(self) -> None:
        """root.sql-private-server"""
        with mock.patch.dict(os.environ, {'PGHOST':'owner.invalid','PGOPTIONS':'invalid fixture option',
                                          'PGPASSWORD':'unused-fictional'}):
            with private_server() as lab:
                lab.server.createdb('fixture')
                lab.run_file('fixture', ROOT / 'contract/1/layout.sql')
                before = lab.dump('fixture')
                self.assertTrue(before)
                self.assertEqual(before, lab.dump('fixture'))
                self.assertEqual(set(lab.environment), {'HOME','PATH','LANG'})
                self.assertEqual(lab.server.value('fixture','SELECT to_json(inet_server_addr() IS NULL)'), True)
                socket, data, home = lab.server.socket_folder, lab.server.data, lab.server.home
                self.assertTrue(socket.is_dir())
        self.assertFalse(socket.exists())
        self.assertFalse(data.exists())
        self.assertFalse(home.exists())
# TEST-TIER-END tests/test_sql_support.py::SqlSupport.test_private_server_ignores_caller_pg_variables_and_dumps_a_stable_schema

# LOW TIER — DO NOT ENABLE OR RECREATE
# Historical examples only. Read before adding related tests; never execute.
# LOW-TIER-BEGIN: tests/mid/test_mid_sql_support.py::SqlSupport.test_each_missing_tool_is_named_before_a_server_can_start
# Reason: Fixture data/default/schema assertions and simple prerequisite/cleanup branches add no distinct information beyond the retained private-server isolation and actual packaged SQL qualification. Case reviewed: root.sql-tools
# Source: arbol-root@ef4fd6a30eca7130653b20e5eedf0da7be72aaa4:tests/mid/test_mid_sql_support.py
# Historical fixtures and class context are available at the source revision; no active dependencies restored.
# LOW-TIER-SOURCE-BEGIN
#     def test_each_missing_tool_is_named_before_a_server_can_start(self) -> None:
#         """root.sql-tools"""
#         for missing in ['initdb','pg_ctl','createdb','psql','pg_dump']:
#             with self.subTest(missing=missing):
#                 def which(name: str, path: str | None = None, *, missing_tool: str = missing) -> str | None:
#                     return None if name == missing_tool else '/fictional-bin/'+name
#                 with mock.patch('scripts.sql_support.shutil.which', side_effect=which):
#                     with mock.patch('scripts.sql_support.Server.create') as create:
#                         with self.assertRaisesRegex(FileNotFoundError, missing):
#                             with private_server(path='/fictional-bin'):
#                                 self.fail('A missing program cannot yield a server.')
#                         create.assert_not_called()
# LOW-TIER-SOURCE-END
# LOW-TIER-END

# LOW-TIER-BEGIN: tests/mid/test_mid_sql_support.py::SqlSupport.test_copied_build_identity_and_lineage_are_validated_before_sql
# Reason: Fixture data/default/schema assertions and simple prerequisite/cleanup branches add no distinct information beyond the retained private-server isolation and actual packaged SQL qualification. Case reviewed: root.sql-input
# Source: arbol-root@ef4fd6a30eca7130653b20e5eedf0da7be72aaa4:tests/mid/test_mid_sql_support.py
# Historical fixtures and class context are available at the source revision; no active dependencies restored.
# LOW-TIER-SOURCE-BEGIN
#     def test_copied_build_identity_and_lineage_are_validated_before_sql(self) -> None:
#         """root.sql-input"""
#         with tempfile.TemporaryDirectory(prefix='root-sql-input-') as temporary:
#             folder = self.image(Path(temporary), older='fictionalold')
#             value = BuildInput.read(folder)
#             self.assertEqual((value.root,value.contract,value.older,value.number), ('fictionalnew',1,'fictionalold','1'))
#             path = folder / 'package-manifest.json'
#             original = json.loads(path.read_text())
#             patches: list[dict[str, object]] = [
#                 {'root':'other'}, {'rootContract':True}, {'rootContract':0}, {'grewFrom':'../other'},
#                 {'grewFrom':'fictionalnew'}]
#             for patch in patches:
#                 with self.subTest(patch=patch):
#                     path.write_text(json.dumps({'layout':{**original['layout'], **patch}}))
#                     with self.assertRaises(ValueError):
#                         BuildInput.read(folder)
#             path.write_text(json.dumps(original))
#             value.file('migrate.sql').unlink()
#             with self.assertRaises(FileNotFoundError):
#                 BuildInput.read(folder)
# LOW-TIER-SOURCE-END
# LOW-TIER-END

# LOW-TIER-BEGIN: tests/mid/test_mid_sql_support.py::SqlSupport.test_nonregular_sql_input_is_never_followed_or_read
# Reason: Fixture data/default/schema assertions and simple prerequisite/cleanup branches add no distinct information beyond the retained private-server isolation and actual packaged SQL qualification. Case reviewed: Nonregular sql input is never followed or read.
# Source: arbol-root@ef4fd6a30eca7130653b20e5eedf0da7be72aaa4:tests/mid/test_mid_sql_support.py
# Historical fixtures and class context are available at the source revision; no active dependencies restored.
# LOW-TIER-SOURCE-BEGIN
#     def test_nonregular_sql_input_is_never_followed_or_read(self) -> None:
#         with tempfile.TemporaryDirectory(prefix='root-sql-input-') as temporary:
#             base = Path(temporary)
#             folder = self.image(base)
#             path = folder / 'layout/root-tables.sql'
#             path.unlink()
#             os.mkfifo(path)
#             with self.assertRaises(ValueError):
#                 BuildInput.read(folder)
#             path.unlink()
#             outside = base / 'outside.sql'
#             outside.write_text('-- unchanged')
#             path.symlink_to(outside)
#             with self.assertRaises(ValueError):
#                 BuildInput.read(folder)
#             self.assertEqual(outside.read_text(), '-- unchanged')
# LOW-TIER-SOURCE-END
# LOW-TIER-END

# LOW-TIER-BEGIN: tests/mid/test_mid_sql_support.py::SqlSupport.test_private_server_is_removed_after_a_failed_check
# Reason: Fixture data/default/schema assertions and simple prerequisite/cleanup branches add no distinct information beyond the retained private-server isolation and actual packaged SQL qualification. Case reviewed: root.sql-cleanup
# Source: arbol-root@ef4fd6a30eca7130653b20e5eedf0da7be72aaa4:tests/mid/test_mid_sql_support.py
# Historical fixtures and class context are available at the source revision; no active dependencies restored.
# LOW-TIER-SOURCE-BEGIN
#     def test_private_server_is_removed_after_a_failed_check(self) -> None:
#         """root.sql-cleanup"""
#         with self.assertRaisesRegex(ValueError, 'planted failure'):
#             with private_server() as lab:
#                 data, socket = lab.server.data, lab.server.socket_folder
#                 raise ValueError('planted failure')
#         self.assertFalse(data.exists())
#         self.assertFalse(socket.exists())
# LOW-TIER-SOURCE-END
# LOW-TIER-END

# LOW-TIER-BEGIN: tests/mid/test_mid_sql_support.py::SqlSupport.test_fictional_rows_cover_replacement_open_history_and_exact_text
# Reason: Fixture data/default/schema assertions and simple prerequisite/cleanup branches add no distinct information beyond the retained private-server isolation and actual packaged SQL qualification. Case reviewed: root.migration-fixture
# Source: arbol-root@ef4fd6a30eca7130653b20e5eedf0da7be72aaa4:tests/mid/test_mid_sql_support.py
# Historical fixtures and class context are available at the source revision; no active dependencies restored.
# LOW-TIER-SOURCE-BEGIN
#     def test_fictional_rows_cover_replacement_open_history_and_exact_text(self) -> None:
#         """root.migration-fixture"""
#         with private_server() as lab:
#             lab.server.createdb('fixture')
#             lab.run_file('fixture', ROOT / 'contract/1/layout.sql')
#             lab.run_file('fixture', ROOT / 'tests/fixtures/migration-root/layout.sql')
#             seed(lab.server, 'fixture')
#             self.assertEqual(len(lab.server.rows('fixture','SELECT * FROM chats')), len(CHATS))
#             exchanges = lab.server.rows('fixture','SELECT id,state,replaced_by FROM exchanges ORDER BY id')
#             self.assertEqual([row['state'] for row in exchanges], ['completed','failed','open','cancelled'])
#             self.assertEqual(exchanges[1]['replaced_by'], EXCHANGES[2])
#             messages = lab.server.rows('fixture','SELECT text FROM messages')
#             self.assertTrue(all(row['text'].endswith(SPECIAL) for row in messages))
#             self.assertEqual(len(lab.server.rows('fixture',"SELECT * FROM runs WHERE exchange_id='"+EXCHANGES[1]+"'")),1)
#             self.assertEqual(lab.server.rows('fixture','SELECT * FROM migrated_chats'), [])
# LOW-TIER-SOURCE-END
# LOW-TIER-END
