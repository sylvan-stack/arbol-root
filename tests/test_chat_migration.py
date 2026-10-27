"""Private qualification of optional Root-owned migration modes; no owner Root or account is used."""

from __future__ import annotations

import contextlib
import json
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from scripts.migration_modes import CAPABILITY, branch, read_modes  # noqa: E402
from scripts.migration_protocol import REQUIRED, protocol  # noqa: E402
from scripts.sql_support import BuildInput, SqlLab  # noqa: E402


class Capabilities(unittest.TestCase):
    def test_explicit_capabilities_are_regular_versioned_and_complete(self) -> None:
        """root.migration-mode-capability"""
        with tempfile.TemporaryDirectory(prefix='private migration capabilities ') as directory:
            path = Path(directory)/'migration-modes.json'
            self.assertIsNone(read_modes(path,optional=True))
            for value in [True,{'version':True,'modes':['check','chat']},{'version':2,'modes':['check','chat']},
                          {'version':1,'modes':['check']},{**CAPABILITY,'unknown':True}]:
                path.write_text(json.dumps(value))
                with self.subTest(value=value),self.assertRaises(ValueError):
                    read_modes(path)
            path.write_text(json.dumps(CAPABILITY))
            self.assertEqual(read_modes(path),CAPABILITY)
            linked = path.with_name('linked.json')
            linked.symlink_to(path)
            with self.assertRaises(ValueError):
                read_modes(linked)
            path.unlink()
            with self.assertRaises(ValueError):
                read_modes(path)

    def test_only_documented_branches_execute_and_legacy_protocol_stays_strict(self) -> None:
        """root.migration-mode-protocol"""
        whole = (ROOT/'tests/fixtures/migration-root/migrate.sql').read_text()
        source = '\\if :{?arbol_migrate_chat}\nSELECT chat_mode;\n\\elif :{?arbol_migrate_check}\nSELECT check_mode;\n\\else\n'+whole+'\\endif\n'
        self.assertEqual(protocol(source),REQUIRED)
        self.assertEqual(branch(source,'chat'),'SELECT chat_mode;\n')
        self.assertEqual(branch(source,'check'),'SELECT check_mode;\n')
        with self.assertRaises(ValueError):
            protocol(source.replace('READ ONLY','READ WRITE'))
        for value in [source.replace('arbol_migrate_chat','unrecognized'),source+'\\else\n',source[:-len('\\endif\n')]]:
            with self.subTest(value=value),self.assertRaises(ValueError):
                branch(value)


class ChatModes(unittest.TestCase):
    scope: contextlib.ExitStack
    lab: SqlLab

    @classmethod
    def setUpClass(cls) -> None:
        from scripts.sql_support import private_server
        cls.scope = contextlib.ExitStack()
        cls.lab = cls.scope.enter_context(private_server())

    @classmethod
    def tearDownClass(cls) -> None:
        cls.scope.close()

    def inputs(self) -> BuildInput:
        from scripts.sql_support import BuildInput
        temporary = tempfile.TemporaryDirectory(prefix='fictional chat modes ')
        self.addCleanup(temporary.cleanup)
        folder = Path(temporary.name)
        (folder/'layout').mkdir()
        (folder/'roots/sapling').mkdir(parents=True)
        for source,name in [('contract/1/layout.sql','chat-tables.sql'),('roots/jensen/layout.sql','root-tables.sql'),
                            ('roots/jensen/migrate.sql','migrate.sql')]:
            shutil.copy2(ROOT/source,folder/'layout'/name)
        shutil.copy2(ROOT/'roots/sapling/layout.sql',folder/'roots/sapling/layout.sql')
        return BuildInput(folder,'jensen','0',1,'sapling',('check','chat'))

    def test_advertised_modes_preserve_history_and_refuse_without_partial_writes(self) -> None:
        """root.migration-chat-modes"""
        from scripts.chat_migration_check import check_modes
        report = check_modes(self.inputs(),self.lab)
        self.assertTrue(report['exactHistory'])
        self.assertTrue(report['continuedPreserved'])
        self.assertEqual(report['busyStatus'],3)

    def test_source_writes_and_unsafe_copy_metadata_fail_before_sql_execution(self) -> None:
        """root.migration-mode-protocol-refusal"""
        from scripts.migration_protocol import mode_protocol
        source = (ROOT/'roots/jensen/migrate.sql').read_text()
        for mode in ['check','chat']:
            mode_protocol(source,mode)
            for altered in [source.replace('READ ONLY','READ WRITE'),
                            source.replace("WITH (FORMAT binary)","WITH (FORMAT text)"),
                            source.replace('\\connect :from_database','\\connect unrelated'),
                            source.replace('\\set QUIET on','\\! touch escaped')]:
                with self.subTest(mode=mode),self.assertRaises(ValueError):
                    mode_protocol(altered,mode)

    def test_planted_history_and_stale_faults_are_detected_by_qualification(self) -> None:
        """root.migration-chat-faults"""
        from scripts.chat_migration_check import check_modes
        for old,new in [("SET stale=(s.ended_through>m.ended_through)","SET stale=false"),
                        ("INSERT INTO messages SELECT * FROM incoming_messages;",
                         "UPDATE incoming_messages SET text='corrupted'; INSERT INTO messages SELECT * FROM incoming_messages;")]:
            inputs = self.inputs()
            script = inputs.file('migrate.sql')
            source = script.read_text()
            self.assertIn(old,source)
            script.write_text(source.replace(old,new))
            with self.subTest(fault=old),self.assertRaisesRegex(ValueError,'Chat migration changed'):
                check_modes(inputs,self.lab)


    def test_failure_after_target_deletion_or_stale_update_rolls_back_all_rows(self) -> None:
        """root.migration-chat-rollback"""
        import uuid

        from scripts.chat_migration_check import history, invoke
        from scripts.migration_fixtures import CHATS, EXCHANGES, seed
        inputs = self.inputs()
        source,target = 'rollback_source_'+uuid.uuid4().hex,'rollback_target_'+uuid.uuid4().hex
        for database in [source,target]:
            self.lab.server.createdb(database)
            self.lab.run_file(database,inputs.file('chat-tables.sql'))
        self.lab.run_file(target,inputs.file('root-tables.sql'))
        seed(self.lab.server,source)
        self.assertEqual(invoke(self.lab,inputs,source,target,'whole').returncode,0)
        self.lab.server.execute(source,f"UPDATE exchanges SET state='completed',ended_at=clock_timestamp() WHERE id='{EXCHANGES[2]}'")
        before,original = history(self.lab,target),history(self.lab,source)
        script = inputs.file('migrate.sql')
        sql = script.read_text()
        for mode,marker in [('chat','DELETE FROM exchanges WHERE chat_id=requested;'),
                            ('check','FROM source_progress s WHERE m.from_chat=s.chat_id AND m.from_root=current_setting(\'arbol.from_root\');')]:
            self.assertIn(marker,sql)
            script.write_text(sql.replace(marker,marker+'\n  PERFORM 1/0;'))
            result = invoke(self.lab,inputs,source,target,mode,CHATS[0])
            self.assertEqual(result.returncode,3,result.stderr)
            self.assertIn('division by zero',result.stderr)
            self.assertEqual(history(self.lab,target),before)
            self.assertEqual(history(self.lab,source),original)
