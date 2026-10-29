"""Mid-tier selections. Write or run only in an explicitly requested testing task."""
from __future__ import annotations

import test_chat_migration as _support


class ChatModes(_support.ChatModes):


# TEST-TIER-BEGIN tests/test_chat_migration.py::ChatModes.test_failure_after_target_deletion_or_stale_update_rolls_back_all_rows
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
        self.lab.run_file(source,inputs.folder/'roots/sapling/layout.sql')
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
# TEST-TIER-END tests/test_chat_migration.py::ChatModes.test_failure_after_target_deletion_or_stale_update_rolls_back_all_rows

# LOW TIER — DO NOT ENABLE OR RECREATE
# Historical examples only. Read before adding related tests; never execute.
# LOW-TIER-BEGIN: tests/mid/test_mid_chat_migration.py::Capabilities.test_explicit_capabilities_are_regular_versioned_and_complete
# Reason: Capability/SQL-text predicate tables and wrapper re-runs add no distinct evidence beyond actual migration qualifiers and injected destructive-transaction rollback. Case reviewed: root.migration-mode-capability
# Source: arbol-root@ef4fd6a30eca7130653b20e5eedf0da7be72aaa4:tests/mid/test_mid_chat_migration.py
# Historical fixtures and class context are available at the source revision; no active dependencies restored.
# LOW-TIER-SOURCE-BEGIN
#     def test_explicit_capabilities_are_regular_versioned_and_complete(self) -> None:
#         """root.migration-mode-capability"""
#         with tempfile.TemporaryDirectory(prefix='private migration capabilities ') as directory:
#             path = Path(directory)/'migration-modes.json'
#             self.assertIsNone(read_modes(path,optional=True))
#             for value in [True,{'version':True,'modes':['check','chat']},{'version':2,'modes':['check','chat']},
#                           {'version':1,'modes':['check']},{**CAPABILITY,'unknown':True}]:
#                 path.write_text(json.dumps(value))
#                 with self.subTest(value=value),self.assertRaises(ValueError):
#                     read_modes(path)
#             path.write_text(json.dumps(CAPABILITY))
#             self.assertEqual(read_modes(path),CAPABILITY)
#             linked = path.with_name('linked.json')
#             linked.symlink_to(path)
#             with self.assertRaises(ValueError):
#                 read_modes(linked)
#             path.unlink()
#             with self.assertRaises(ValueError):
#                 read_modes(path)
# LOW-TIER-SOURCE-END
# LOW-TIER-END

# LOW-TIER-BEGIN: tests/mid/test_mid_chat_migration.py::Capabilities.test_only_documented_branches_execute_and_legacy_protocol_stays_strict
# Reason: Capability/SQL-text predicate tables and wrapper re-runs add no distinct evidence beyond actual migration qualifiers and injected destructive-transaction rollback. Case reviewed: root.migration-mode-protocol
# Source: arbol-root@ef4fd6a30eca7130653b20e5eedf0da7be72aaa4:tests/mid/test_mid_chat_migration.py
# Historical fixtures and class context are available at the source revision; no active dependencies restored.
# LOW-TIER-SOURCE-BEGIN
#     def test_only_documented_branches_execute_and_legacy_protocol_stays_strict(self) -> None:
#         """root.migration-mode-protocol"""
#         whole = (ROOT/'tests/fixtures/migration-root/migrate.sql').read_text()
#         source = '\\if :{?arbol_migrate_chat}\nSELECT chat_mode;\n\\elif :{?arbol_migrate_check}\nSELECT check_mode;\n\\else\n'+whole+'\\endif\n'
#         self.assertEqual(protocol(source),REQUIRED)
#         self.assertEqual(branch(source,'chat'),'SELECT chat_mode;\n')
#         self.assertEqual(branch(source,'check'),'SELECT check_mode;\n')
#         with self.assertRaises(ValueError):
#             protocol(source.replace('READ ONLY','READ WRITE'))
#         for value in [source.replace('arbol_migrate_chat','unrecognized'),source+'\\else\n',source[:-len('\\endif\n')]]:
#             with self.subTest(value=value),self.assertRaises(ValueError):
#                 branch(value)
# LOW-TIER-SOURCE-END
# LOW-TIER-END

# LOW-TIER-BEGIN: tests/mid/test_mid_chat_migration.py::Capabilities.test_build_input_refuses_boolean_or_mismatched_advertised_versions
# Reason: Capability/SQL-text predicate tables and wrapper re-runs add no distinct evidence beyond actual migration qualifiers and injected destructive-transaction rollback. Case reviewed: root.migration-mode-input
# Source: arbol-root@ef4fd6a30eca7130653b20e5eedf0da7be72aaa4:tests/mid/test_mid_chat_migration.py
# Historical fixtures and class context are available at the source revision; no active dependencies restored.
# LOW-TIER-SOURCE-BEGIN
#     def test_build_input_refuses_boolean_or_mismatched_advertised_versions(self) -> None:
#         """root.migration-mode-input"""
#         import test_sql_support
#         with tempfile.TemporaryDirectory() as directory:
#             folder = test_sql_support.SqlSupport.image(Path(directory),older='fictionalold')
#             capability = folder/'layout/migration-modes.json'
#             capability.write_text(json.dumps(CAPABILITY))
#             manifest = folder/'package-manifest.json'
#             value = json.loads(manifest.read_text())
#             for advertised in [{'version':True,'modes':['check','chat']},{'version':2,'modes':['check','chat']}]:
#                 value['layout']['migrationModes'] = advertised
#                 manifest.write_text(json.dumps(value))
#                 with self.subTest(advertised=advertised),self.assertRaises(ValueError):
#                     BuildInput.read(folder)
#             value['layout']['migrationModes'] = CAPABILITY
#             manifest.write_text(json.dumps(value))
#             self.assertEqual(BuildInput.read(folder).modes,('check','chat'))
# LOW-TIER-SOURCE-END
# LOW-TIER-END

# LOW-TIER-BEGIN: tests/mid/test_mid_chat_migration.py::ChatModes.test_advertised_modes_preserve_history_and_refuse_without_partial_writes
# Reason: Capability/SQL-text predicate tables and wrapper re-runs add no distinct evidence beyond actual migration qualifiers and injected destructive-transaction rollback. Case reviewed: root.migration-chat-modes
# Source: arbol-root@ef4fd6a30eca7130653b20e5eedf0da7be72aaa4:tests/mid/test_mid_chat_migration.py
# Historical fixtures and class context are available at the source revision; no active dependencies restored.
# LOW-TIER-SOURCE-BEGIN
#     def test_advertised_modes_preserve_history_and_refuse_without_partial_writes(self) -> None:
#         """root.migration-chat-modes"""
#         from scripts.chat_migration_check import check_modes
#         report = check_modes(self.inputs(),self.lab)
#         self.assertTrue(report['exactHistory'])
#         self.assertTrue(report['continuedPreserved'])
#         self.assertEqual(report['busyStatus'],3)
# LOW-TIER-SOURCE-END
# LOW-TIER-END

# LOW-TIER-BEGIN: tests/mid/test_mid_chat_migration.py::ChatModes.test_source_writes_and_unsafe_copy_metadata_fail_before_sql_execution
# Reason: Capability/SQL-text predicate tables and wrapper re-runs add no distinct evidence beyond actual migration qualifiers and injected destructive-transaction rollback. Case reviewed: root.migration-mode-protocol-refusal
# Source: arbol-root@ef4fd6a30eca7130653b20e5eedf0da7be72aaa4:tests/mid/test_mid_chat_migration.py
# Historical fixtures and class context are available at the source revision; no active dependencies restored.
# LOW-TIER-SOURCE-BEGIN
#     def test_source_writes_and_unsafe_copy_metadata_fail_before_sql_execution(self) -> None:
#         """root.migration-mode-protocol-refusal"""
#         from scripts.migration_protocol import mode_protocol
#         source = (ROOT/'roots/jensen/migrate.sql').read_text()
#         for mode in ['check','chat']:
#             mode_protocol(source,mode)
#             for altered in [source.replace('READ ONLY','READ WRITE'),
#                             source.replace("WITH (FORMAT binary)","WITH (FORMAT text)"),
#                             source.replace('\\connect :from_database','\\connect unrelated'),
#                             source.replace('\\set QUIET on','\\! touch escaped')]:
#                 with self.subTest(mode=mode),self.assertRaises(ValueError):
#                     mode_protocol(altered,mode)
# LOW-TIER-SOURCE-END
# LOW-TIER-END

# LOW-TIER-BEGIN: tests/mid/test_mid_chat_migration.py::ChatModes.test_planted_history_and_stale_faults_are_detected_by_qualification
# Reason: Capability/SQL-text predicate tables and wrapper re-runs add no distinct evidence beyond actual migration qualifiers and injected destructive-transaction rollback. Case reviewed: root.migration-chat-faults
# Source: arbol-root@ef4fd6a30eca7130653b20e5eedf0da7be72aaa4:tests/mid/test_mid_chat_migration.py
# Historical fixtures and class context are available at the source revision; no active dependencies restored.
# LOW-TIER-SOURCE-BEGIN
#     def test_planted_history_and_stale_faults_are_detected_by_qualification(self) -> None:
#         """root.migration-chat-faults"""
#         from scripts.chat_migration_check import check_modes
#         for old,new in [("SET stale=(s.ended_through>m.ended_through)","SET stale=false"),
#                         ("INSERT INTO messages SELECT * FROM incoming_messages;",
#                          "UPDATE incoming_messages SET text='corrupted'; INSERT INTO messages SELECT * FROM incoming_messages;")]:
#             inputs = self.inputs()
#             script = inputs.file('migrate.sql')
#             source = script.read_text()
#             self.assertIn(old,source)
#             script.write_text(source.replace(old,new))
#             with self.subTest(fault=old),self.assertRaisesRegex(ValueError,'Chat migration changed'):
#                 check_modes(inputs,self.lab)
# LOW-TIER-SOURCE-END
# LOW-TIER-END
