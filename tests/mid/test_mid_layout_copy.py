"""Commented mid-tier selections; see MID_TIER.md before restoring a case."""

# Restore the needed imports and class header only for an explicit testing task.
# import test_layout_copy as _support
# from test_layout_copy import (
#     LayoutCopy,
#     Path,
#     copy_layout,
#     json,
#     sys,
#     tempfile,
#     unittest,
# )


# class LayoutCopy(_support.LayoutCopy):
# TEST-TIER-DISABLED-BEGIN tests/test_layout_copy.py::LayoutCopy.test_exact_version_and_root_files_and_no_migration_without_lineage
#     def test_exact_version_and_root_files_and_no_migration_without_lineage(self) -> None:
#         """root.layout-copy"""
#         (self.folder / 'layout').mkdir()
#         (self.folder / 'layout/migrate.sql').write_text('stale')
#         self.assertEqual(self.copy(), {'root':'second', 'rootContract':2, 'grewFrom':None})
#         self.assertEqual((self.folder / 'layout/chat-tables.sql').read_bytes(),
#                          (self.repo / 'contract/2/layout.sql').read_bytes())
#         self.assertEqual((self.folder / 'layout/root-tables.sql').read_bytes(), b'-- Root\n')
#         self.assertFalse((self.folder / 'layout/migrate.sql').exists())
# TEST-TIER-DISABLED-END tests/test_layout_copy.py::LayoutCopy.test_exact_version_and_root_files_and_no_migration_without_lineage

# TEST-TIER-DISABLED-BEGIN tests/test_layout_copy.py::LayoutCopy.test_lineage_requires_and_copies_migration_exactly
#     def test_lineage_requires_and_copies_migration_exactly(self) -> None:
#         """root.layout-lineage"""
#         self.metadata['grewFrom'] = 'sapling'
#         self.write_root()
#         self.copy()
#         self.assertEqual((self.folder / 'layout/migrate.sql').read_bytes(), b'-- migrate\n')
#         (self.repo / 'roots/second/migrate.sql').unlink()
#         with self.assertRaisesRegex(ValueError, 'Missing regular SQL'):
#             self.copy()
# TEST-TIER-DISABLED-END tests/test_layout_copy.py::LayoutCopy.test_lineage_requires_and_copies_migration_exactly

# TEST-TIER-DISABLED-BEGIN tests/test_layout_copy.py::LayoutCopy.test_every_missing_file_fails_before_any_copy
#     def test_every_missing_file_fails_before_any_copy(self) -> None:
#         """root.layout-missing"""
#         for name in ['contract/2/layout.sql', 'roots/second/layout.sql']:
#             path = self.repo / name
#             data = path.read_bytes()
#             path.unlink()
#             with self.subTest(name=name), self.assertRaisesRegex(ValueError, 'Missing regular SQL'):
#                 self.copy()
#             self.assertFalse((self.folder / 'layout').exists())
#             path.write_bytes(data)
# TEST-TIER-DISABLED-END tests/test_layout_copy.py::LayoutCopy.test_every_missing_file_fails_before_any_copy

# TEST-TIER-DISABLED-BEGIN tests/test_layout_copy.py::LayoutCopy.test_bad_root_contract_lineage_and_identity_cannot_escape_source
#     def test_bad_root_contract_lineage_and_identity_cannot_escape_source(self) -> None:
#         """root.layout-metadata"""
#         for key, bad in [('rootContract',True), ('rootContract',0), ('rootContract','../x'),
#                          ('root','other'), ('grewFrom','../x'), ('grewFrom','second'), ('grewFrom',None)]:
#             with self.subTest(key=key, bad=bad):
#                 original = self.metadata.copy()
#                 self.metadata[key] = bad
#                 self.write_root()
#                 with self.assertRaises(ValueError):
#                     self.copy()
#                 self.metadata = original
#         self.write_root()
#         (self.folder / 'build.json').write_text(json.dumps({**self.record, 'root':'../second'}))
#         with self.assertRaises(ValueError):
#             self.copy()
#         self.assertFalse((self.folder / 'layout').exists())
# TEST-TIER-DISABLED-END tests/test_layout_copy.py::LayoutCopy.test_bad_root_contract_lineage_and_identity_cannot_escape_source

# TEST-TIER-DISABLED-BEGIN tests/test_layout_copy.py::LayoutCopy.test_optional_modes_copy_exactly_and_bad_or_lineageless_capabilities_write_nothing
#     def test_optional_modes_copy_exactly_and_bad_or_lineageless_capabilities_write_nothing(self) -> None:
#         """root.layout-migration-modes"""
#         from scripts.migration_modes import CAPABILITY
#         descriptor = self.repo/'roots/second/migration-modes.json'
#         descriptor.write_text(json.dumps(CAPABILITY,indent=1)+'\n')
#         with self.assertRaises(ValueError):
#             self.copy()
#         self.assertFalse((self.folder/'layout').exists())
#         self.metadata['grewFrom']='sapling'
#         self.write_root()
#         for value in [{'version':True,'modes':['check','chat']},{'version':1,'modes':['chat']}]:
#             descriptor.write_text(json.dumps(value))
#             with self.assertRaises(ValueError):
#                 self.copy()
#             self.assertFalse((self.folder/'layout').exists())
#         descriptor.write_text(json.dumps(CAPABILITY,indent=1)+'\n')
#         self.assertEqual(self.copy()['migrationModes'],CAPABILITY)
#         copied = self.folder/'layout/migration-modes.json'
#         self.assertEqual(copied.read_bytes(),descriptor.read_bytes())
#         descriptor.unlink()
#         self.assertNotIn('migrationModes',self.copy())
#         self.assertFalse(copied.exists())
# TEST-TIER-DISABLED-END tests/test_layout_copy.py::LayoutCopy.test_optional_modes_copy_exactly_and_bad_or_lineageless_capabilities_write_nothing


raise RuntimeError("Mid-tier tests require an explicitly requested testing task; see MID_TIER.md.")
