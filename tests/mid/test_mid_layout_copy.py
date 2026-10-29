
# LOW TIER — DO NOT ENABLE OR RECREATE
# Historical examples only. Read before adding related tests; never execute.
# LOW-TIER-BEGIN: tests/mid/test_mid_layout_copy.py::LayoutCopy.test_exact_version_and_root_files_and_no_migration_without_lineage
# Reason: Copy equality and metadata validation variants restate straightforward code and repeat packaged SQL integrity/relocation checks. Case reviewed: root.layout-copy
# Source: arbol-root@ef4fd6a30eca7130653b20e5eedf0da7be72aaa4:tests/mid/test_mid_layout_copy.py
# Historical fixtures and class context are available at the source revision; no active dependencies restored.
# LOW-TIER-SOURCE-BEGIN
#     def test_exact_version_and_root_files_and_no_migration_without_lineage(self) -> None:
#         """root.layout-copy"""
#         (self.folder / 'layout').mkdir()
#         (self.folder / 'layout/migrate.sql').write_text('stale')
#         self.assertEqual(self.copy(), {'root':'second', 'rootContract':2, 'grewFrom':None})
#         self.assertEqual((self.folder / 'layout/chat-tables.sql').read_bytes(),
#                          (self.repo / 'contract/2/layout.sql').read_bytes())
#         self.assertEqual((self.folder / 'layout/root-tables.sql').read_bytes(), b'-- Root\n')
#         self.assertFalse((self.folder / 'layout/migrate.sql').exists())
# LOW-TIER-SOURCE-END
# LOW-TIER-END

# LOW-TIER-BEGIN: tests/mid/test_mid_layout_copy.py::LayoutCopy.test_lineage_requires_and_copies_migration_exactly
# Reason: Copy equality and metadata validation variants restate straightforward code and repeat packaged SQL integrity/relocation checks. Case reviewed: root.layout-lineage
# Source: arbol-root@ef4fd6a30eca7130653b20e5eedf0da7be72aaa4:tests/mid/test_mid_layout_copy.py
# Historical fixtures and class context are available at the source revision; no active dependencies restored.
# LOW-TIER-SOURCE-BEGIN
#     def test_lineage_requires_and_copies_migration_exactly(self) -> None:
#         """root.layout-lineage"""
#         self.metadata['grewFrom'] = 'sapling'
#         self.write_root()
#         self.copy()
#         self.assertEqual((self.folder / 'layout/migrate.sql').read_bytes(), b'-- migrate\n')
#         (self.repo / 'roots/second/migrate.sql').unlink()
#         with self.assertRaisesRegex(ValueError, 'Missing regular SQL'):
#             self.copy()
# LOW-TIER-SOURCE-END
# LOW-TIER-END

# LOW-TIER-BEGIN: tests/mid/test_mid_layout_copy.py::LayoutCopy.test_every_missing_file_fails_before_any_copy
# Reason: Copy equality and metadata validation variants restate straightforward code and repeat packaged SQL integrity/relocation checks. Case reviewed: root.layout-missing
# Source: arbol-root@ef4fd6a30eca7130653b20e5eedf0da7be72aaa4:tests/mid/test_mid_layout_copy.py
# Historical fixtures and class context are available at the source revision; no active dependencies restored.
# LOW-TIER-SOURCE-BEGIN
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
# LOW-TIER-SOURCE-END
# LOW-TIER-END

# LOW-TIER-BEGIN: tests/mid/test_mid_layout_copy.py::LayoutCopy.test_bad_root_contract_lineage_and_identity_cannot_escape_source
# Reason: Copy equality and metadata validation variants restate straightforward code and repeat packaged SQL integrity/relocation checks. Case reviewed: root.layout-metadata
# Source: arbol-root@ef4fd6a30eca7130653b20e5eedf0da7be72aaa4:tests/mid/test_mid_layout_copy.py
# Historical fixtures and class context are available at the source revision; no active dependencies restored.
# LOW-TIER-SOURCE-BEGIN
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
# LOW-TIER-SOURCE-END
# LOW-TIER-END

# LOW-TIER-BEGIN: tests/mid/test_mid_layout_copy.py::LayoutCopy.test_optional_modes_copy_exactly_and_bad_or_lineageless_capabilities_write_nothing
# Reason: Copy equality and metadata validation variants restate straightforward code and repeat packaged SQL integrity/relocation checks. Case reviewed: root.layout-migration-modes
# Source: arbol-root@ef4fd6a30eca7130653b20e5eedf0da7be72aaa4:tests/mid/test_mid_layout_copy.py
# Historical fixtures and class context are available at the source revision; no active dependencies restored.
# LOW-TIER-SOURCE-BEGIN
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
# LOW-TIER-SOURCE-END
# LOW-TIER-END
