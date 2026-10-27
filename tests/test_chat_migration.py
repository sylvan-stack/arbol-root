"""Private qualification of optional Root-owned migration modes; no owner Root or account is used."""

from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from scripts.migration_modes import CAPABILITY, branch, read_modes  # noqa: E402
from scripts.migration_protocol import REQUIRED, protocol  # noqa: E402


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
