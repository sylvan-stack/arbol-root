
# LOW TIER — DO NOT ENABLE OR RECREATE
# Historical examples only. Read before adding related tests; never execute.
# LOW-TIER-BEGIN: tests/mid/test_mid_migration_protocol.py::MigrationProtocol.test_prescribed_script_uses_two_private_connections_and_relative_binary_copies
# Reason: Literal protocol substitution tables mirror the parser; actual isolated migration qualification separately proves source read-only behavior and transactional preservation. Case reviewed: root.migration-protocol
# Source: arbol-root@ef4fd6a30eca7130653b20e5eedf0da7be72aaa4:tests/mid/test_mid_migration_protocol.py
# Historical fixtures and class context are available at the source revision; no active dependencies restored.
# LOW-TIER-SOURCE-BEGIN
#     def test_prescribed_script_uses_two_private_connections_and_relative_binary_copies(self) -> None:
#         """root.migration-protocol"""
#         source = (ROOT / 'tests/fixtures/migration-root/migrate.sql').read_text()
#         self.assertEqual(protocol(source),REQUIRED)
# LOW-TIER-SOURCE-END
# LOW-TIER-END

# LOW-TIER-BEGIN: tests/mid/test_mid_migration_protocol.py::MigrationProtocol.test_connection_file_and_transaction_faults_are_refused_before_execution
# Reason: Literal protocol substitution tables mirror the parser; actual isolated migration qualification separately proves source read-only behavior and transactional preservation. Case reviewed: root.migration-protocol-refusal
# Source: arbol-root@ef4fd6a30eca7130653b20e5eedf0da7be72aaa4:tests/mid/test_mid_migration_protocol.py
# Historical fixtures and class context are available at the source revision; no active dependencies restored.
# LOW-TIER-SOURCE-BEGIN
#     def test_connection_file_and_transaction_faults_are_refused_before_execution(self) -> None:
#         """root.migration-protocol-refusal"""
#         source = (ROOT / 'tests/fixtures/migration-root/migrate.sql').read_text()
#         broken = [
#             source.replace('\\connect :from_database','\\connect postgresql://owner.invalid/database'),
#             source.replace("'chats.copy'","'/tmp/outside.copy'"),
#             source.replace('REPEATABLE READ READ ONLY','READ COMMITTED READ WRITE'),
#             source.replace('BEGIN;','BEGIN;\nCOMMIT;\nBEGIN;'),
#             source.replace('\\copy chats FROM', '\\! echo forbidden\n\\copy chats FROM'),
#             source.replace("TO 'chats.copy'", "TO PROGRAM 'chats.copy'"),
#             source.replace('\\copy runs FROM', '-- missing copy\n-- \\copy runs FROM'),
#             source.replace('COMMIT;','COMMIT;\nSELECT 1;',1),
#         ]
#         for text in broken:
#             with self.subTest(text=text),self.assertRaises(ValueError):
#                 protocol(text)
# LOW-TIER-SOURCE-END
# LOW-TIER-END
