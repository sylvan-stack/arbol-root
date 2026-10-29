"""Mid-tier selections. Write or run only in an explicitly requested testing task."""
from __future__ import annotations

import test_migration_protocol as _support
from test_migration_protocol import (
    MigrationProtocol,
    Path,
    REQUIRED,
    ROOT,
    protocol,
    sys,
    unittest,
)


class MigrationProtocol(_support.MigrationProtocol):
# TEST-TIER-BEGIN tests/test_migration_protocol.py::MigrationProtocol.test_prescribed_script_uses_two_private_connections_and_relative_binary_copies
    def test_prescribed_script_uses_two_private_connections_and_relative_binary_copies(self) -> None:
        """root.migration-protocol"""
        source = (ROOT / 'tests/fixtures/migration-root/migrate.sql').read_text()
        self.assertEqual(protocol(source),REQUIRED)
# TEST-TIER-END tests/test_migration_protocol.py::MigrationProtocol.test_prescribed_script_uses_two_private_connections_and_relative_binary_copies

# TEST-TIER-BEGIN tests/test_migration_protocol.py::MigrationProtocol.test_connection_file_and_transaction_faults_are_refused_before_execution
    def test_connection_file_and_transaction_faults_are_refused_before_execution(self) -> None:
        """root.migration-protocol-refusal"""
        source = (ROOT / 'tests/fixtures/migration-root/migrate.sql').read_text()
        broken = [
            source.replace('\\connect :from_database','\\connect postgresql://owner.invalid/database'),
            source.replace("'chats.copy'","'/tmp/outside.copy'"),
            source.replace('REPEATABLE READ READ ONLY','READ COMMITTED READ WRITE'),
            source.replace('BEGIN;','BEGIN;\nCOMMIT;\nBEGIN;'),
            source.replace('\\copy chats FROM', '\\! echo forbidden\n\\copy chats FROM'),
            source.replace("TO 'chats.copy'", "TO PROGRAM 'chats.copy'"),
            source.replace('\\copy runs FROM', '-- missing copy\n-- \\copy runs FROM'),
            source.replace('COMMIT;','COMMIT;\nSELECT 1;',1),
        ]
        for text in broken:
            with self.subTest(text=text),self.assertRaises(ValueError):
                protocol(text)
# TEST-TIER-END tests/test_migration_protocol.py::MigrationProtocol.test_connection_file_and_transaction_faults_are_refused_before_execution
