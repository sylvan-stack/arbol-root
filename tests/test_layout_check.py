from __future__ import annotations

import contextlib
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import test_sql_support  # noqa: E402

from scripts.check_layout import run_layout  # noqa: E402
from scripts.sql_statements import layout_statements, preserves, statements  # noqa: E402
from scripts.sql_support import BuildInput, SqlLab, private_server  # noqa: E402


class Statements(unittest.TestCase):
    def test_semicolons_comments_case_and_quoted_contents_have_distinct_meanings(self) -> None:
        """root.layout-statements"""
        first = "COMMENT ON TABLE t IS 'A; -- kept /*literal*/''quote'; /* outer /* inner */ end */"
        other = " comment\non table T is 'A; -- kept /*literal*/''quote' ; -- ignored\n"
        self.assertEqual(statements(first), statements(other))
        with self.assertRaises(ValueError):
            preserves(first, first.replace('A;', 'a;'))
        preserves(first, first+"\nCOMMENT ON COLUMN t.x IS 'new';")
        self.assertEqual(len(statements("COMMENT ON TABLE t IS $$semi; -- text$$;")), 1)
        layout_statements('ALTER TABLE t ADD COLUMN IF NOT EXISTS x numeric(10,2) DEFAULT 1;')

    def test_incomplete_statements_client_commands_and_data_writes_are_refused(self) -> None:
        """root.layout-ddl-boundary"""
        for source in ["COMMENT ON TABLE t IS 'broken;", '/* broken', 'CREATE TABLE t(id integer)',
                       '\\connect owner\n', 'INSERT INTO t VALUES(1);', 'DELETE FROM t;',
                       'CREATE TABLE copy AS SELECT * FROM t;',
                       'ALTER TABLE t ADD COLUMN IF NOT EXISTS x integer, DROP COLUMN y;']:
            with self.subTest(source=source), self.assertRaises(ValueError):
                layout_statements(source)


class LayoutCheck(unittest.TestCase):
    scope: contextlib.ExitStack
    lab: SqlLab

    @classmethod
    def setUpClass(cls) -> None:
        cls.scope = contextlib.ExitStack()
        cls.lab = cls.scope.enter_context(private_server())

    @classmethod
    def tearDownClass(cls) -> None:
        cls.scope.close()

    def inputs(self, own: str | None = None) -> BuildInput:
        temporary = tempfile.TemporaryDirectory(prefix='root-layout-input-')
        self.addCleanup(temporary.cleanup)
        folder = test_sql_support.SqlSupport.image(Path(temporary.name))
        shutil.copy2(ROOT / 'contract/1/layout.sql', folder / 'layout/chat-tables.sql')
        target = folder / 'layout/root-tables.sql'
        if own is None:
            shutil.copy2(ROOT / 'tests/fixtures/migration-root/layout.sql', target)
        else:
            target.write_text(own)
        return BuildInput.read(folder)

    def test_both_packaged_files_run_twice_with_stable_dump_and_comments(self) -> None:
        """root.layout-idempotence"""
        report = run_layout(self.inputs(), self.lab)
        self.assertEqual(report, {'check':'layout','root':'fictionalnew','repeated':True,'earlierBuild':None})

    def test_a_nonrepeatable_statement_fails_on_its_second_run(self) -> None:
        """root.layout-not-repeatable"""
        own = ("CREATE TABLE fictional(id integer);"
               "COMMENT ON TABLE fictional IS 'Fictional'; COMMENT ON COLUMN fictional.id IS 'Identity';")
        with self.assertRaisesRegex(RuntimeError, 'already exists'):
            run_layout(self.inputs(own), self.lab)

    def test_every_table_and_column_needs_a_comment(self) -> None:
        """root.layout-comments"""
        for own in ["CREATE TABLE IF NOT EXISTS fictional(id integer);",
                    "CREATE TABLE IF NOT EXISTS fictional(id integer); COMMENT ON TABLE fictional IS 'Fictional';"]:
            with self.subTest(own=own), self.assertRaisesRegex(ValueError, 'comment'):
                run_layout(self.inputs(own), self.lab)

    def test_a_client_command_cannot_create_a_database_or_connect_elsewhere(self) -> None:
        inputs = self.inputs('\\connect owner\n')
        with mock.patch.object(self.lab.server, 'createdb') as create:
            with self.assertRaises(ValueError):
                run_layout(inputs, self.lab)
        create.assert_not_called()

    def test_check_entry_bootstraps_its_own_source_path_before_refusing_an_incomplete_image(self) -> None:
        """root.layout-entry"""
        with tempfile.TemporaryDirectory(prefix='root-layout-entry-') as temporary:
            folder = Path(temporary)
            for name in ['src','scripts','contract']:
                shutil.copytree(ROOT / name,folder / name,ignore=shutil.ignore_patterns('__pycache__','*.pyc'))
            answer = subprocess.run([sys.executable,'-I','-B',str(folder / 'scripts/check_layout.py')],
                                    capture_output=True,text=True,check=False,timeout=10)
            self.assertEqual(answer.returncode,1)
            self.assertIn('layout check failed:',answer.stderr)
            self.assertNotIn('Traceback',answer.stderr)
