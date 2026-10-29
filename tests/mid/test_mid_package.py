"""Commented mid-tier selections; see MID_TIER.md before restoring a case."""

# Restore the needed imports and class header only for an explicit testing task.
# import test_package as _support
# from test_package import (
#     Package,
#     Path,
#     ROOT,
#     digest,
#     json,
#     mock,
#     os,
#     shutil,
#     sys,
#     tarfile,
#     target,
#     tempfile,
#     unittest,
# )


# class Package(_support.Package):
# TEST-TIER-DISABLED-BEGIN tests/test_package.py::Package.test_package_contains_only_own_assets_runtime_and_complete_file_hashes
#     def test_package_contains_only_own_assets_runtime_and_complete_file_hashes(self) -> None:
#         """root.package"""
#         with mock.patch('urllib.request.urlopen') as network:
#             package(str(self.folder), root=self.source)
#         network.assert_not_called()
#         manifest = json.loads((self.folder / 'package-manifest.json').read_text())
#         self.assertEqual((manifest['build'], manifest['candidate'], manifest['dependencies']), ('0',True,{}))
#         for name in ['bin/arbol-root', 'src/arbol_root/cli.py', 'tests/standin_trunk.py', 'scripts/build.py',
#                      'contract/1/layout.sql', 'contract/conformance/tests/test_layout.py',
#                      'contract/conformance/specifications/03-the-chat-tables.md', 'roots/sapling/layout.sql',
#                      'runtime/python/bin/python3.14']:
#             self.assertEqual(manifest['files'][name], digest(self.folder / name))
#         with self.assertRaisesRegex(ValueError, 'already holds'):
#             package(str(self.folder), root=self.source)
# TEST-TIER-DISABLED-END tests/test_package.py::Package.test_package_contains_only_own_assets_runtime_and_complete_file_hashes

# TEST-TIER-DISABLED-BEGIN tests/test_package.py::Package.test_relocated_shell_entry_execs_own_python_with_arguments_and_same_pid
#     def test_relocated_shell_entry_execs_own_python_with_arguments_and_same_pid(self) -> None:
#         """root.package-entry"""
#         package(str(self.folder), root=self.source)
#         moved = self.base / 'moved package with spaces'
#         self.folder.rename(moved)
#         report = self.base / 'report'
#         args = ['trunks', '', 'two words', '-leading']
#         proc = subprocess.Popen([str(moved / 'bin/arbol-root'), *args],
#                                 env={**os.environ, 'PACKAGE_REPORT':str(report)})
#         self.assertEqual(proc.wait(timeout=10), 0)
#         self.assertEqual(report.read_text().splitlines(), [str(proc.pid),'-I','-B',str(moved / 'bin/entry.py'),*args])
# TEST-TIER-DISABLED-END tests/test_package.py::Package.test_relocated_shell_entry_execs_own_python_with_arguments_and_same_pid

# TEST-TIER-DISABLED-BEGIN tests/test_package.py::Package.test_numbered_image_is_verified_after_sql_copy_and_tampering_is_detected
#     def test_numbered_image_is_verified_after_sql_copy_and_tampering_is_detected(self) -> None:
#         """root.package-integrity"""
#         record = {'component':'arbol-root','entry':'bin/arbol-root','packageVersion':'1.0.0','build':'a','root':'sapling'}
#         (self.folder / 'build.json').write_text(json.dumps(record))
#         with mock.patch.dict(os.environ, {'ARBOL_BUILD_DIR':str(self.folder), 'ARBOL_BUILD_NUMBER':'a'}):
#             package(root=self.source)
#         home = self.base / 'home'
#         root_file = home / 'Library/Application Support/Arbol/roots/sapling/root.json'
#         root_file.parent.mkdir(parents=True)
#         root_file.write_text('{"root":"sapling", "rootContract":1}')
#         layout = copy_layout(self.folder, root=self.source, home=home)
#         write_manifest(self.folder, layout)
#         verify(self.folder)
#         record['status'] = 'working'
#         (self.folder / 'build.json').write_text(json.dumps(record))
#         (self.folder / 'build.log').write_text('mutable')
#         (self.folder / 'last-start').write_text('mutable')
#         verify(self.folder)
#         path = self.folder / 'layout/chat-tables.sql'
#         old = path.read_bytes()
#         path.write_bytes(b'changed')
#         with self.assertRaisesRegex(ValueError, 'manifest'):
#             verify(self.folder)
#         path.write_bytes(old)
#         record['root'] = 'other'
#         (self.folder / 'build.json').write_text(json.dumps(record))
#         with self.assertRaisesRegex(ValueError, 'identity'):
#             verify(self.folder)
# TEST-TIER-DISABLED-END tests/test_package.py::Package.test_numbered_image_is_verified_after_sql_copy_and_tampering_is_detected

# TEST-TIER-DISABLED-BEGIN tests/test_package.py::Package.test_bad_cached_digest_and_untrusted_archive_pin_are_refused
#     def test_bad_cached_digest_and_untrusted_archive_pin_are_refused(self) -> None:
#         """root.package-pin"""
#         pin = json.loads((self.source / 'scripts/python-distribution.json').read_text())['distributions'][target()]
#         (self.cache / (pin['sha256']+'.tar.gz')).write_text('damaged')
#         with mock.patch('urllib.request.urlopen') as network, self.assertRaisesRegex(ValueError,'SHA-256'):
#             archive(pin)
#         network.assert_not_called()
#         for distribution in [{'url':'https://unrelated.invalid/python','sha256':'a'*64},
#                              {'url':pin['url'], 'sha256':'bad'}]:
#             with self.subTest(distribution=distribution), self.assertRaises(ValueError):
#                 archive(distribution)
#         self.assertEqual(list(self.folder.iterdir()), [])
# TEST-TIER-DISABLED-END tests/test_package.py::Package.test_bad_cached_digest_and_untrusted_archive_pin_are_refused

# TEST-TIER-DISABLED-BEGIN tests/test_package.py::Package.test_metadata_overlap_and_bad_numbered_identity_are_refused
#     def test_metadata_overlap_and_bad_numbered_identity_are_refused(self) -> None:
#         with self.assertRaisesRegex(ValueError, 'overlap'):
#             package(str(self.source), root=self.source)
#         (self.folder / 'build.json').write_text('{"component":"arbol-root", "build":"a", "root":"../x"}')
#         with mock.patch.dict(os.environ, {'ARBOL_BUILD_DIR':str(self.folder), 'ARBOL_BUILD_NUMBER':'a'}):
#             with self.assertRaisesRegex(ValueError,'identity'):
#                 package(root=self.source)
#         project = self.source / 'pyproject.toml'
#         project.write_text(project.read_text().replace('dependencies = []', 'dependencies = ["external"]'))
#         with self.assertRaisesRegex(ValueError,'standard-library'):
#             metadata(self.source)
# TEST-TIER-DISABLED-END tests/test_package.py::Package.test_metadata_overlap_and_bad_numbered_identity_are_refused


# Original deferred imports (restore at the required scope, never blindly at the tail).
# TEST-TIER-IMPORTS-BEGIN tests/test_package.py:6
# import subprocess
# TEST-TIER-IMPORTS-END tests/test_package.py:6

# TEST-TIER-IMPORTS-BEGIN tests/test_package.py:15
# from scripts.build import copy_layout  # noqa: E402
# TEST-TIER-IMPORTS-END tests/test_package.py:15

# TEST-TIER-IMPORTS-BEGIN tests/test_package.py:16
# from scripts.package_build import archive, package  # noqa: E402
# TEST-TIER-IMPORTS-END tests/test_package.py:16

# TEST-TIER-IMPORTS-BEGIN tests/test_package.py:17
# from scripts.package_support import digest, metadata, target, verify, write_manifest  # noqa: E402
# TEST-TIER-IMPORTS-END tests/test_package.py:17

raise RuntimeError("Mid-tier tests require an explicitly requested testing task; see MID_TIER.md.")
