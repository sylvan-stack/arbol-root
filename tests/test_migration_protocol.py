from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from scripts.migration_protocol import REQUIRED, protocol  # noqa: E402


class MigrationProtocol(unittest.TestCase):
    def test_prescribed_script_uses_two_private_connections_and_relative_binary_copies(self) -> None:
        """root.migration-protocol"""
        source = (ROOT / 'tests/fixtures/migration-root/migrate.sql').read_text()
        self.assertEqual(protocol(source),REQUIRED)

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
