from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))



class Boundary(unittest.TestCase):
    pass  # TEST-TIER-EMPTY-SUITE; helpers remain importable.
# TEST-TIER-DISABLED-BEGIN tests/test_management_boundary.py::Boundary.test_every_command_uses_private_root_identity_without_payload_settings_or_retained_manager_files
#     def test_every_command_uses_private_root_identity_without_payload_settings_or_retained_manager_files(self) -> None:
#         """root.management-boundary"""
#         f = Fixture(self)
#         settings = f.base / '.arbol/roots/sapling'
#         settings.mkdir(parents=True)
#         for path in [settings / 'arbol-root.json', settings / 'arbol.json', f.base / '.arbol/database.json']:
#             os.mkfifo(path)
#         value = record(1)
#         folder = f.put(value)
#         for name in ['events.jsonl','route.json','request.json']:
#             os.mkfifo(folder / name)
#         before = sorted(str(p.relative_to(f.root)) for p in f.root.rglob('*'))
#         original = (folder / 'record.json').read_bytes()
#         request = f.base / 'incoming request'
#         os.mkfifo(request)
#         script = json.loads((f.bin / 'script.json').read_text())
#         script['responses']['run'] = {'stdout':json.dumps({'accepted':True,'root':'sapling'})+'\n'}
#         (f.bin / 'script.json').write_text(json.dumps(script))
#         commands = [('trunks',), ('start','--exchange',record(2)['exchange'],'--request',str(request)),
#                     ('list',), ('stop',value['exchange']), ('settle',value['exchange']), ('settle',)]
#         for args in commands:
#             with self.subTest(command=args[0]):
#                 reply = f.cli(*args)
#                 self.assertEqual(reply.returncode, 0, reply.stderr)
#                 self.assertEqual(json.loads(reply.stdout)['root'], 'sapling')
#         self.assertFalse(request.exists())
#         self.assertEqual(sorted(str(p.relative_to(f.root)) for p in f.root.rglob('*')), before)
#         self.assertEqual((folder / 'record.json').read_bytes(), original)
#         self.assertEqual((folder / 'control').read_bytes(), b'')
#         self.assertEqual(sorted(p.name for p in settings.iterdir()), ['arbol-root.json','arbol.json'])
# TEST-TIER-DISABLED-END tests/test_management_boundary.py::Boundary.test_every_command_uses_private_root_identity_without_payload_settings_or_retained_manager_files

# TEST-TIER-DISABLED-BEGIN tests/test_management_boundary.py::Boundary.test_a_failed_record_stat_is_a_structured_refusal
#     def test_a_failed_record_stat_is_a_structured_refusal(self) -> None:
#         """root.stop-record-io"""
#         f = Fixture(self)
#         value = record(1)
#         f.put(value)
#         with mock.patch('arbol_root.stop.os.stat', side_effect=PermissionError('private fixture')):
#             with self.assertRaises(Refusal) as error:
#                 read_exchange(f.context, value['exchange'])
#         self.assertEqual(error.exception.code, 'root_unavailable')
# TEST-TIER-DISABLED-END tests/test_management_boundary.py::Boundary.test_a_failed_record_stat_is_a_structured_refusal

# Archived complete imports; restore needed names in their original scope, not at this file tail.
# TEST-TIER-IMPORTS-BEGIN tests/test_management_boundary.py:3
# import json
# TEST-TIER-IMPORTS-END tests/test_management_boundary.py:3
# TEST-TIER-IMPORTS-BEGIN tests/test_management_boundary.py:4
# import os
# TEST-TIER-IMPORTS-END tests/test_management_boundary.py:4
# TEST-TIER-IMPORTS-BEGIN tests/test_management_boundary.py:8
# from unittest import mock
# TEST-TIER-IMPORTS-END tests/test_management_boundary.py:8
# TEST-TIER-IMPORTS-BEGIN tests/test_management_boundary.py:11
# from management_support import Fixture  # noqa: E402
# TEST-TIER-IMPORTS-END tests/test_management_boundary.py:11
# TEST-TIER-IMPORTS-BEGIN tests/test_management_boundary.py:12
# from test_listing import record  # noqa: E402
# TEST-TIER-IMPORTS-END tests/test_management_boundary.py:12
# TEST-TIER-IMPORTS-BEGIN tests/test_management_boundary.py:14
# from arbol_root.model import Refusal  # noqa: E402
# TEST-TIER-IMPORTS-END tests/test_management_boundary.py:14
# TEST-TIER-IMPORTS-BEGIN tests/test_management_boundary.py:15
# from arbol_root.stop import read_exchange  # noqa: E402
# TEST-TIER-IMPORTS-END tests/test_management_boundary.py:15
