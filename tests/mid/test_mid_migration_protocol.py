"""Commented mid-tier selections; see MID_TIER.md before restoring a case."""

# Restore the needed imports and class header only for an explicit testing task.
# import test_migration_protocol as _support
# from test_migration_protocol import (
#     MigrationProtocol,
#     Path,
#     ROOT,
#     sys,
#     unittest,
# )


# class MigrationProtocol(_support.MigrationProtocol):
# TEST-TIER-DISABLED-BEGIN tests/test_migration_protocol.py::MigrationProtocol.test_prescribed_script_uses_two_private_connections_and_relative_binary_copies
#     def test_prescribed_script_uses_two_private_connections_and_relative_binary_copies(self) -> None:
#         """root.migration-protocol"""
#         source = (ROOT / 'tests/fixtures/migration-root/migrate.sql').read_text()
#         self.assertEqual(protocol(source),REQUIRED)
# TEST-TIER-DISABLED-END tests/test_migration_protocol.py::MigrationProtocol.test_prescribed_script_uses_two_private_connections_and_relative_binary_copies

# TEST-TIER-DISABLED-BEGIN tests/test_migration_protocol.py::MigrationProtocol.test_connection_file_and_transaction_faults_are_refused_before_execution
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
# TEST-TIER-DISABLED-END tests/test_migration_protocol.py::MigrationProtocol.test_connection_file_and_transaction_faults_are_refused_before_execution


# Original deferred imports (restore at the required scope, never blindly at the tail).
# TEST-TIER-IMPORTS-BEGIN tests/test_migration_protocol.py:9
# from scripts.migration_protocol import REQUIRED, protocol  # noqa: E402
# TEST-TIER-IMPORTS-END tests/test_migration_protocol.py:9

raise RuntimeError("Mid-tier tests require an explicitly requested testing task; see MID_TIER.md.")
