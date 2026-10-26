from __future__ import annotations

import contextlib
import json
import shutil
import stat
import sys
import tempfile
import unittest
from pathlib import Path
from typing import Any
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
import test_sql_support  # noqa: E402

from scripts.check_migration import Origin, check_migration, origin, run_migration  # noqa: E402
from scripts.sql_support import BuildInput, SqlLab, private_server  # noqa: E402


class MigrationCheck(unittest.TestCase):
    scope: contextlib.ExitStack
    lab: SqlLab

    @classmethod
    def setUpClass(cls) -> None:
        cls.scope = contextlib.ExitStack()
        cls.lab = cls.scope.enter_context(private_server())

    @classmethod
    def tearDownClass(cls) -> None:
        cls.scope.close()

    def inputs(self) -> tuple[BuildInput,Origin,Path]:
        temporary = tempfile.TemporaryDirectory(prefix='root-migration-input-')
        self.addCleanup(temporary.cleanup)
        base = Path(temporary.name)
        folder = test_sql_support.SqlSupport.image(base,older='fictionalold')
        for name in ['layout.sql','migrate.sql']:
            target = 'root-tables.sql' if name == 'layout.sql' else name
            shutil.copy2(ROOT / 'tests/fixtures/migration-root' / name,folder / 'layout' / target)
        shutil.copy2(ROOT / 'contract/1/layout.sql',folder / 'layout/chat-tables.sql')
        (folder / 'contract/1').mkdir(parents=True)
        shutil.copy2(ROOT / 'contract/1/layout.sql',folder / 'contract/1/layout.sql')
        (folder / 'roots/fictionalold').mkdir(parents=True)
        shutil.copy2(ROOT / 'roots/sapling/layout.sql',folder / 'roots/fictionalold/layout.sql')
        home = base / 'private-home'
        header = home / 'Library/Application Support/Arbol/roots/fictionalold'
        header.mkdir(parents=True)
        (header / 'root.json').write_text('{"root":"fictionalold","rootContract":1}')
        inputs = BuildInput.read(folder)
        return inputs,origin(inputs,home),home

    def test_whole_protocol_preserves_rows_text_snapshot_provenance_rollback_and_repeat(self) -> None:
        """root.migration-whole"""
        inputs,older,_home = self.inputs()
        working: list[Path] = []
        original = self.lab.run_file

        def observed(*args: Any,**kwargs: Any) -> Any:
            if kwargs.get('variables'):
                path = kwargs['cwd']
                self.assertEqual(stat.S_IMODE(path.stat().st_mode),0o700)
                self.assertEqual(set(self.lab.environment),{'HOME','PATH','LANG'})
                self.assertEqual(set(kwargs['variables']),{'from_database','from_root'})
                working.append(path)
            return original(*args,**kwargs)

        with mock.patch.object(self.lab,'run_file',side_effect=observed):
            report = run_migration(inputs,self.lab,older)
        self.assertEqual(report,{'check':'migration','root':'fictionalnew','olderRoot':'fictionalold',
                                 'sourceUnchanged':True,'unchangedTables':5,'sourceRows':19,
                                 'interruptedExchanges':1,'provenanceRows':2,
                                 'missingSourceStatus':3,'missingTableStatus':3,'repeatable':True})
        self.assertEqual(len(working),4)
        self.assertTrue(all(not path.exists() for path in working))

    def test_a_root_without_lineage_passes_without_a_server_or_tools(self) -> None:
        """root.migration-no-lineage"""
        with tempfile.TemporaryDirectory(prefix='root-migration-input-') as temporary:
            inputs = BuildInput.read(test_sql_support.SqlSupport.image(Path(temporary)))
            with mock.patch('scripts.check_migration.private_server') as server:
                report = check_migration(inputs)
            self.assertEqual(report,{'check':'migration','root':'fictionalnew','olderRoot':None,'serverNeeded':False})
            server.assert_not_called()

    def test_parent_identity_and_layout_inputs_are_required_before_starting_a_server(self) -> None:
        """root.migration-origin"""
        inputs,_older,home = self.inputs()
        header = home / 'Library/Application Support/Arbol/roots/fictionalold/root.json'
        for value in [{'root':'other','rootContract':1},{'root':'fictionalold','rootContract':True}]:
            header.write_text(json.dumps(value))
            with mock.patch('scripts.check_migration.private_server') as server:
                with self.assertRaises(ValueError):
                    check_migration(inputs,home=home)
            server.assert_not_called()
        header.write_text('{"root":"fictionalold","rootContract":1}')
        (inputs.folder / 'contract/1/layout.sql').unlink()
        with self.assertRaises(FileNotFoundError):
            origin(inputs,home)

    def test_corrupting_copied_text_fails_the_actual_row_judgment(self) -> None:
        """root.migration-text-fault"""
        inputs,older,_home = self.inputs()
        script = inputs.file('migrate.sql')
        text = script.read_text().rsplit('COMMIT;',1)
        script.write_text(text[0]+"\nUPDATE messages SET text='corrupted';\nCOMMIT;"+text[1])
        with self.assertRaisesRegex(ValueError,'exact text/JSON'):
            run_migration(inputs,self.lab,older)

    def test_wrong_provenance_fails_the_actual_row_judgment(self) -> None:
        """root.migration-provenance-fault"""
        inputs,older,_home = self.inputs()
        script = inputs.file('migrate.sql')
        script.write_text(script.read_text().replace("SELECT c.id, :'from_root', c.id,",
                                                     "SELECT c.id, 'fictionalwrong', c.id,"))
        with self.assertRaisesRegex(ValueError,'provenance'):
            run_migration(inputs,self.lab,older)

    def test_an_open_exchange_must_be_interrupted_at_the_snapshot(self) -> None:
        """root.migration-open-fault"""
        inputs,older,_home = self.inputs()
        script = inputs.file('migrate.sql')
        script.write_text(script.read_text().replace("SET state = 'interrupted'","SET state = 'cancelled'"))
        with self.assertRaisesRegex(ValueError,'public.exchanges'):
            run_migration(inputs,self.lab,older)

    def test_a_snapshot_outside_the_run_is_rejected_even_if_both_times_match(self) -> None:
        """root.migration-snapshot-fault"""
        inputs,older,_home = self.inputs()
        script = inputs.file('migrate.sql')
        script.write_text(script.read_text().replace(":'snapshot'","'2000-01-01T00:00:00Z'"))
        with self.assertRaisesRegex(ValueError,'snapshot'):
            run_migration(inputs,self.lab,older)
