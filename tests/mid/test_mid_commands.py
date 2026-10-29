"""Commented mid-tier selections; see MID_TIER.md before restoring a case."""

# Restore the needed imports and class header only for an explicit testing task.
# import test_commands as _support
# from test_commands import (
#     Commands,
#     Path,
#     REPO,
#     json,
#     os,
#     shlex,
#     shutil,
#     subprocess,
#     sys,
#     tempfile,
#     unittest,
# )


# class Commands(_support.Commands):
# TEST-TIER-DISABLED-BEGIN tests/test_commands.py::Commands.test_trunks_forwards_reply_bytes_exact_arguments_and_launcher_path
#     def test_trunks_forwards_reply_bytes_exact_arguments_and_launcher_path(self) -> None:
#         """root.trunks"""
#         answer = self.run_cli([*self.common, 'trunks', 'advanced'])
#         self.assertEqual(answer.returncode, 0, answer.stderr)
#         self.assertEqual(answer.stdout, '  { "root": "sapling", "trunks": [], "extra": "🌲" }\n'.encode())
#         call = json.loads((self.bin_dir / 'calls.jsonl').read_text())
#         self.assertEqual(call['args'], ['--root', 'sapling', 'advanced', 'list'])
#         self.assertEqual(call['path'].split(os.pathsep)[0], str(self.bin_dir))
#         self.assertEqual(call['home'], str(self.home))
# TEST-TIER-DISABLED-END tests/test_commands.py::Commands.test_trunks_forwards_reply_bytes_exact_arguments_and_launcher_path

# TEST-TIER-DISABLED-BEGIN tests/test_commands.py::Commands.test_refusal_available_and_stderr_pass_through
#     def test_refusal_available_and_stderr_pass_through(self) -> None:
#         """root.trunks-refusal"""
#         line = '{ "error": {"code":"no_fit", "message":"none"}, "available":["a"] }\n'
#         self.script(stdout=line, stderr='diagnostic\n', status=9)
#         reply = self.run_cli(['trunks', *self.common])
#         self.assertEqual((reply.returncode, reply.stdout, reply.stderr), (1, line.encode(), b'diagnostic\n'))
# TEST-TIER-DISABLED-END tests/test_commands.py::Commands.test_refusal_available_and_stderr_pass_through

# TEST-TIER-DISABLED-BEGIN tests/test_commands.py::Commands.test_first_object_line_is_the_reply_and_nonzero_status_is_not_success
#     def test_first_object_line_is_the_reply_and_nonzero_status_is_not_success(self) -> None:
#         self.script(stdout='diagnostic\n[1]\n{ "root":"sapling" }\n{"ignored":true}\n', status=2)
#         reply = self.run_cli(['trunks', *self.common])
#         self.assertEqual((reply.returncode, reply.stdout), (1, b'{ "root":"sapling" }\n'))
#         self.script(stdout='{"error":{"code":"unknown_trunk"}}', status=0)
#         self.assertEqual(self.run_cli(['trunks', *self.common]).returncode, 1)
# TEST-TIER-DISABLED-END tests/test_commands.py::Commands.test_first_object_line_is_the_reply_and_nonzero_status_is_not_success

# TEST-TIER-DISABLED-BEGIN tests/test_commands.py::Commands.test_missing_unexecutable_and_no_object_are_unavailable
#     def test_missing_unexecutable_and_no_object_are_unavailable(self) -> None:
#         """root.trunk-unavailable"""
#         for text in ['', '[]\n42\nnull\n', '{bad}\n']:
#             with self.subTest(text=text):
#                 self.script(stdout=text)
#                 self.refusal(['trunks', *self.common], 'trunk_unavailable')
#         (self.bin_dir / 'arbol-trunk').chmod(0o600)
#         self.refusal(['trunks', *self.common], 'trunk_unavailable')
#         (self.bin_dir / 'arbol-trunk').unlink()
#         self.refusal(['trunks', *self.common], 'trunk_unavailable')
# TEST-TIER-DISABLED-END tests/test_commands.py::Commands.test_missing_unexecutable_and_no_object_are_unavailable

# TEST-TIER-DISABLED-BEGIN tests/test_commands.py::Commands.test_options_accept_both_forms_and_either_side_but_reject_duplicates
#     def test_options_accept_both_forms_and_either_side_but_reject_duplicates(self) -> None:
#         """root.input"""
#         self.assertEqual(self.run_cli(['--root=sapling', 'trunks', '--root-dir='+str(self.root_dir),
#                                       '--bin-dir='+str(self.bin_dir)]).returncode, 0)
#         for args in [[], ['unknown'], ['trunks', 'a', 'b'], ['trunks', '--other'], ['trunks', '--root'],
#                      ['trunks', '--root='], ['trunks', '--root', '-x'], ['trunks', '-v', 'a'],
#                      ['trunks', '--root', 'sapling', '--root=sapling']]:
#             with self.subTest(args=args):
#                 self.refusal(args, 'invalid_input')
# TEST-TIER-DISABLED-END tests/test_commands.py::Commands.test_options_accept_both_forms_and_either_side_but_reject_duplicates

# TEST-TIER-DISABLED-BEGIN tests/test_commands.py::Commands.test_root_selection_is_explicit_and_root_dir_requires_bin_dir
#     def test_root_selection_is_explicit_and_root_dir_requires_bin_dir(self) -> None:
#         """root.identity"""
#         self.refusal(['trunks'], 'invalid_input', package=self.development)
#         for name in ['../sapling', 'Sapling', 'two words', 'a-b', '']:
#             with self.subTest(name=name):
#                 self.refusal(['trunks', '--root='+name], 'invalid_input')
#         self.refusal(['trunks', '--root', 'sapling', '--root-dir', str(self.root_dir)], 'invalid_input')
#         value = identity(self.development, {'--root': 'sapling', '--root-dir': str(self.root_dir), '--bin-dir': str(self.bin_dir)})
#         self.assertEqual((value.root, value.build, value.version), ('sapling', '0', '1.0.0'))
# TEST-TIER-DISABLED-END tests/test_commands.py::Commands.test_root_selection_is_explicit_and_root_dir_requires_bin_dir

# TEST-TIER-DISABLED-BEGIN tests/test_commands.py::Commands.test_damaged_missing_nonregular_or_mismatched_root_is_unknown
#     def test_damaged_missing_nonregular_or_mismatched_root_is_unknown(self) -> None:
#         record = self.root_dir / 'root.json'
#         for text in ['not json', '[]', '{}', '{"root":"other"}']:
#             with self.subTest(text=text):
#                 record.write_text(text)
#                 self.refusal(['trunks', *self.common], 'unknown_root')
#         record.unlink()
#         self.refusal(['trunks', *self.common], 'unknown_root')
#         record.mkdir()
#         self.refusal(['trunks', *self.common], 'unknown_root')
#         record.rmdir()
#         os.mkfifo(record)
#         self.refusal(['trunks', *self.common], 'unknown_root')
# TEST-TIER-DISABLED-END tests/test_commands.py::Commands.test_damaged_missing_nonregular_or_mismatched_root_is_unknown

# TEST-TIER-DISABLED-BEGIN tests/test_commands.py::Commands.test_build_identity_is_adjacent_and_not_from_environment
#     def test_build_identity_is_adjacent_and_not_from_environment(self) -> None:
#         """root.build-identity"""
#         package = self.home / 'package'
#         package.mkdir()
#         for name in ['src', 'bin']:
#             shutil.copytree(REPO / name, package / name, ignore=shutil.ignore_patterns('__pycache__'))
#         shutil.copy2(REPO / 'package.json', package / 'package.json')
#         record = {'component':'arbol-root','entry':'bin/arbol-root','build':'a','root':'sapling','packageVersion':'1.0.0'}
#         (package / 'build.json').write_text(json.dumps(record))
#         options = {'--root-dir':str(self.root_dir), '--bin-dir':str(self.bin_dir)}
#         context = identity(package, options)
#         self.assertEqual((context.root, context.build), ('sapling', 'a'))
#         self.assertEqual(self.run_cli(['trunks', '--root-dir', str(self.root_dir), '--bin-dir', str(self.bin_dir)],
#                                       package=package).returncode, 0)
#         self.refusal(['trunks', *self.common, '--root=other'], 'invalid_input', package=package)
#         self.refusal(['trunks', '--root', 'other'], 'invalid_input', package=package)
#         for key, bad in [('root','../x'), ('build','0'), ('component','arbol'), ('entry','other'),
#                          ('packageVersion','2.0.0')]:
#             with self.subTest(key=key):
#                 (package / 'build.json').write_text(json.dumps({**record, key:bad}))
#                 self.refusal(['trunks', *self.common], 'invalid_input', package=package)
#         (package / 'build.json').write_text('{bad}')
#         self.refusal(['trunks', *self.common], 'invalid_input', package=package)
# TEST-TIER-DISABLED-END tests/test_commands.py::Commands.test_build_identity_is_adjacent_and_not_from_environment

# TEST-TIER-DISABLED-BEGIN tests/test_commands.py::Commands.test_no_settings_or_exchange_payload_is_opened
#     def test_no_settings_or_exchange_payload_is_opened(self) -> None:
#         """root.no-settings"""
#         settings = self.home / '.arbol/roots/sapling'
#         settings.mkdir(parents=True)
#         for path in [settings / 'arbol-root.json', settings / 'arbol.json', self.home / '.arbol/database.json',
#                      self.root_dir / 'exchanges']:
#             os.mkfifo(path)
#         self.assertEqual(self.run_cli(['trunks', *self.common]).returncode, 0)
# TEST-TIER-DISABLED-END tests/test_commands.py::Commands.test_no_settings_or_exchange_payload_is_opened


# Original deferred imports (restore at the required scope, never blindly at the tail).
# TEST-TIER-IMPORTS-BEGIN tests/test_commands.py:14
# from arbol_root.model import identity  # noqa: E402
# TEST-TIER-IMPORTS-END tests/test_commands.py:14

raise RuntimeError("Mid-tier tests require an explicitly requested testing task; see MID_TIER.md.")
