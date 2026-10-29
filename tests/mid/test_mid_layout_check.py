"""Commented mid-tier selections; see MID_TIER.md before restoring a case."""

# Restore the needed imports and class header only for an explicit testing task.
# import test_layout_check as _support
# from test_layout_check import (
#     BuildInput,
#     LayoutCheck,
#     Path,
#     ROOT,
#     SqlLab,
#     Statements,
#     contextlib,
#     private_server,
#     shutil,
#     sys,
#     tempfile,
#     test_sql_support,
#     unittest,
# )


# class Statements(_support.Statements):
# TEST-TIER-DISABLED-BEGIN tests/test_layout_check.py::Statements.test_semicolons_comments_case_and_quoted_contents_have_distinct_meanings
#     def test_semicolons_comments_case_and_quoted_contents_have_distinct_meanings(self) -> None:
#         """root.layout-statements"""
#         first = "COMMENT ON TABLE t IS 'A; -- kept /*literal*/''quote'; /* outer /* inner */ end */"
#         other = " comment\non table T is 'A; -- kept /*literal*/''quote' ; -- ignored\n"
#         self.assertEqual(statements(first), statements(other))
#         with self.assertRaises(ValueError):
#             preserves(first, first.replace('A;', 'a;'))
#         preserves(first, first+"\nCOMMENT ON COLUMN t.x IS 'new';")
#         self.assertEqual(len(statements("COMMENT ON TABLE t IS $$semi; -- text$$;")), 1)
#         layout_statements('ALTER TABLE t ADD COLUMN IF NOT EXISTS x numeric(10,2) DEFAULT 1;')
# TEST-TIER-DISABLED-END tests/test_layout_check.py::Statements.test_semicolons_comments_case_and_quoted_contents_have_distinct_meanings

# TEST-TIER-DISABLED-BEGIN tests/test_layout_check.py::Statements.test_incomplete_statements_client_commands_and_data_writes_are_refused
#     def test_incomplete_statements_client_commands_and_data_writes_are_refused(self) -> None:
#         """root.layout-ddl-boundary"""
#         for source in ["COMMENT ON TABLE t IS 'broken;", '/* broken', 'CREATE TABLE t(id integer)',
#                        '\\connect owner\n', 'INSERT INTO t VALUES(1);', 'DELETE FROM t;',
#                        'CREATE TABLE copy AS SELECT * FROM t;',
#                        'ALTER TABLE t ADD COLUMN IF NOT EXISTS x integer, DROP COLUMN y;']:
#             with self.subTest(source=source), self.assertRaises(ValueError):
#                 layout_statements(source)
# TEST-TIER-DISABLED-END tests/test_layout_check.py::Statements.test_incomplete_statements_client_commands_and_data_writes_are_refused



# class LayoutCheck(_support.LayoutCheck):
# TEST-TIER-DISABLED-BEGIN tests/test_layout_check.py::LayoutCheck.test_both_packaged_files_run_twice_with_stable_dump_and_comments
#     def test_both_packaged_files_run_twice_with_stable_dump_and_comments(self) -> None:
#         """root.layout-idempotence"""
#         report = run_layout(self.inputs(), self.lab)
#         self.assertEqual(report, {'check':'layout','root':'fictionalnew','repeated':True,'earlierBuild':None})
# TEST-TIER-DISABLED-END tests/test_layout_check.py::LayoutCheck.test_both_packaged_files_run_twice_with_stable_dump_and_comments

# TEST-TIER-DISABLED-BEGIN tests/test_layout_check.py::LayoutCheck.test_a_nonrepeatable_statement_fails_on_its_second_run
#     def test_a_nonrepeatable_statement_fails_on_its_second_run(self) -> None:
#         """root.layout-not-repeatable"""
#         own = ("CREATE TABLE fictional(id integer);"
#                "COMMENT ON TABLE fictional IS 'Fictional'; COMMENT ON COLUMN fictional.id IS 'Identity';")
#         with self.assertRaisesRegex(RuntimeError, 'already exists'):
#             run_layout(self.inputs(own), self.lab)
# TEST-TIER-DISABLED-END tests/test_layout_check.py::LayoutCheck.test_a_nonrepeatable_statement_fails_on_its_second_run

# TEST-TIER-DISABLED-BEGIN tests/test_layout_check.py::LayoutCheck.test_a_sequence_requires_its_comment_and_a_repeatable_create
#     def test_a_sequence_requires_its_comment_and_a_repeatable_create(self) -> None:
#         """root.layout-sequence-comments"""
#         with self.assertRaisesRegex(ValueError, 'Every sequence'):
#             run_layout(self.inputs('CREATE SEQUENCE IF NOT EXISTS fictional_counter;'),self.lab)
#         report=run_layout(self.inputs("CREATE SEQUENCE IF NOT EXISTS fictional_counter; "
#                                      "COMMENT ON SEQUENCE fictional_counter IS 'Fictional counter';"),self.lab)
#         self.assertTrue(report['repeated'])
#         with self.assertRaises(ValueError):
#             layout_statements('CREATE SEQUENCE nonrepeatable;')
# TEST-TIER-DISABLED-END tests/test_layout_check.py::LayoutCheck.test_a_sequence_requires_its_comment_and_a_repeatable_create

# TEST-TIER-DISABLED-BEGIN tests/test_layout_check.py::LayoutCheck.test_every_table_and_column_needs_a_comment
#     def test_every_table_and_column_needs_a_comment(self) -> None:
#         """root.layout-comments"""
#         for own in ["CREATE TABLE IF NOT EXISTS fictional(id integer);",
#                     "CREATE TABLE IF NOT EXISTS fictional(id integer); COMMENT ON TABLE fictional IS 'Fictional';"]:
#             with self.subTest(own=own), self.assertRaisesRegex(ValueError, 'comment'):
#                 run_layout(self.inputs(own), self.lab)
# TEST-TIER-DISABLED-END tests/test_layout_check.py::LayoutCheck.test_every_table_and_column_needs_a_comment

# TEST-TIER-DISABLED-BEGIN tests/test_layout_check.py::LayoutCheck.test_a_client_command_cannot_create_a_database_or_connect_elsewhere
#     def test_a_client_command_cannot_create_a_database_or_connect_elsewhere(self) -> None:
#         inputs = self.inputs('\\connect owner\n')
#         with mock.patch.object(self.lab.server, 'createdb') as create:
#             with self.assertRaises(ValueError):
#                 run_layout(inputs, self.lab)
#         create.assert_not_called()
# TEST-TIER-DISABLED-END tests/test_layout_check.py::LayoutCheck.test_a_client_command_cannot_create_a_database_or_connect_elsewhere

# TEST-TIER-DISABLED-BEGIN tests/test_layout_check.py::LayoutCheck.test_check_entry_bootstraps_its_own_source_path_before_refusing_an_incomplete_image
#     def test_check_entry_bootstraps_its_own_source_path_before_refusing_an_incomplete_image(self) -> None:
#         """root.layout-entry"""
#         with tempfile.TemporaryDirectory(prefix='root-layout-entry-') as temporary:
#             folder = Path(temporary)
#             for name in ['src','scripts','contract']:
#                 shutil.copytree(ROOT / name,folder / name,ignore=shutil.ignore_patterns('__pycache__','*.pyc'))
#             answer = subprocess.run([sys.executable,'-I','-B',str(folder / 'scripts/check_layout.py')],
#                                     capture_output=True,text=True,check=False,timeout=10)
#             self.assertEqual(answer.returncode,1)
#             self.assertIn('layout check failed:',answer.stderr)
#             self.assertNotIn('Traceback',answer.stderr)
# TEST-TIER-DISABLED-END tests/test_layout_check.py::LayoutCheck.test_check_entry_bootstraps_its_own_source_path_before_refusing_an_incomplete_image


# Original deferred imports (restore at the required scope, never blindly at the tail).
# TEST-TIER-IMPORTS-BEGIN tests/test_layout_check.py:5
# import subprocess
# TEST-TIER-IMPORTS-END tests/test_layout_check.py:5

# TEST-TIER-IMPORTS-BEGIN tests/test_layout_check.py:10
# from unittest import mock
# TEST-TIER-IMPORTS-END tests/test_layout_check.py:10

# TEST-TIER-IMPORTS-BEGIN tests/test_layout_check.py:16
# from scripts.check_layout import run_layout  # noqa: E402
# TEST-TIER-IMPORTS-END tests/test_layout_check.py:16

# TEST-TIER-IMPORTS-BEGIN tests/test_layout_check.py:17
# from scripts.sql_statements import layout_statements, preserves, statements  # noqa: E402
# TEST-TIER-IMPORTS-END tests/test_layout_check.py:17

raise RuntimeError("Mid-tier tests require an explicitly requested testing task; see MID_TIER.md.")
