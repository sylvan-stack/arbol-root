"""Commented mid-tier selections; see MID_TIER.md before restoring a case."""

# Restore the needed imports and class header only for an explicit testing task.
# import test_cleanup as _support
# from test_cleanup import (
#     Cleaning,
#     Fixture,
#     Path,
#     os,
#     record,
#     sys,
#     unittest,
# )


# class Cleaning(_support.Cleaning):
# TEST-TIER-DISABLED-BEGIN tests/test_cleanup.py::Cleaning.test_committed_old_folder_goes_without_reading_any_payload
#     def test_committed_old_folder_goes_without_reading_any_payload(self) -> None:
#         """root.cleanup-old"""
#         folder = self.dot(1, 'old', -10)
#         for name in ['record.json', 'events.jsonl', 'control']:
#             os.mkfifo(folder / name)
#         with mock.patch('arbol_root.cleanup.read_record', side_effect=AssertionError('must not read')):
#             self.assertTrue(cleanup(self.f.context, now=1000))
#         self.assertFalse(folder.exists())
# TEST-TIER-DISABLED-END tests/test_cleanup.py::Cleaning.test_committed_old_folder_goes_without_reading_any_payload

# TEST-TIER-DISABLED-BEGIN tests/test_cleanup.py::Cleaning.test_new_age_is_strict_and_future_and_living_folders_stay
#     def test_new_age_is_strict_and_future_and_living_folders_stay(self) -> None:
#         """root.cleanup-new-age"""
#         old = self.dot(1, age=15.001)
#         exact, young, future = self.dot(2, age=15), self.dot(3, age=1), self.dot(4, age=-1)
#         dead, alive = self.dot(5), self.dot(6)
#         for number, folder in [(5, dead), (6, alive)]:
#             (folder / 'record.json').write_text(json.dumps(record(number, pid=456 if number == 5 else 123)))
#             os.utime(folder, (980,980))
#         def actual(pid: int) -> datetime | None:
#             return datetime(2026,10,26,9,tzinfo=UTC) if pid == 123 else None
#         with mock.patch('arbol_root.process.started_at', side_effect=actual):
#             self.assertTrue(cleanup(self.f.context, now=1000))
#         self.assertFalse(old.exists())
#         self.assertFalse(dead.exists())
#         self.assertTrue(all(folder.is_dir() for folder in [exact, young, future, alive]))
# TEST-TIER-DISABLED-END tests/test_cleanup.py::Cleaning.test_new_age_is_strict_and_future_and_living_folders_stay

# TEST-TIER-DISABLED-BEGIN tests/test_cleanup.py::Cleaning.test_uncertain_new_record_never_authorizes_removal
#     def test_uncertain_new_record_never_authorizes_removal(self) -> None:
#         """root.cleanup-unreadable"""
#         folders = []
#         for number, kind in enumerate(['json', 'fifo', 'symlink', 'identity', 'process'], 1):
#             folder = self.dot(number)
#             folders.append(folder)
#             path = folder / 'record.json'
#             if kind == 'json':
#                 path.write_text('{bad}')
#             elif kind == 'fifo':
#                 os.mkfifo(path)
#             elif kind == 'symlink':
#                 path.symlink_to(self.f.base / 'missing-outside')
#             elif kind == 'identity':
#                 path.write_text(json.dumps(record(number, root='other')))
#             else:
#                 path.write_text(json.dumps(record(number)))
#             os.utime(folder, (980,980))
#         with contextlib.redirect_stderr(io.StringIO()) as errors:
#             with mock.patch('arbol_root.process.started_at', side_effect=ValueError('unknown process')):
#                 self.assertFalse(cleanup(self.f.context, now=1000))
#         self.assertTrue(errors.getvalue())
#         self.assertTrue(all(folder.is_dir() for folder in folders))
# TEST-TIER-DISABLED-END tests/test_cleanup.py::Cleaning.test_uncertain_new_record_never_authorizes_removal

# TEST-TIER-DISABLED-BEGIN tests/test_cleanup.py::Cleaning.test_symlink_and_non_uuid_names_cannot_remove_an_outside_folder
#     def test_symlink_and_non_uuid_names_cannot_remove_an_outside_folder(self) -> None:
#         """root.cleanup-paths"""
#         outside = self.f.base / 'outside'
#         outside.mkdir()
#         (outside / 'untouched').write_text('private fixture')
#         link = self.f.exchanges / ('.'+record(1)['exchange']+'.old')
#         link.symlink_to(outside, target_is_directory=True)
#         other = self.f.exchanges / '.not-a-uuid.old'
#         other.mkdir()
#         self.assertTrue(cleanup(self.f.context, now=1000))
#         self.assertEqual((outside / 'untouched').read_text(), 'private fixture')
#         self.assertTrue(link.is_symlink())
#         self.assertTrue(other.is_dir())
# TEST-TIER-DISABLED-END tests/test_cleanup.py::Cleaning.test_symlink_and_non_uuid_names_cannot_remove_an_outside_folder

# TEST-TIER-DISABLED-BEGIN tests/test_cleanup.py::Cleaning.test_named_settle_keeps_dot_folders_but_empty_all_settle_cleans_without_a_launcher
#     def test_named_settle_keeps_dot_folders_but_empty_all_settle_cleans_without_a_launcher(self) -> None:
#         """root.cleanup-all-only"""
#         folder = self.dot(1, 'old')
#         self.assertEqual(settle(self.f.context, record(2)['exchange']).status, 0)
#         self.assertTrue(folder.is_dir())
#         (self.f.bin / 'arbol-trunk').unlink()
#         self.assertEqual(settle(self.f.context).value, {'root':'sapling','results':[]})
#         self.assertFalse(folder.exists())
# TEST-TIER-DISABLED-END tests/test_cleanup.py::Cleaning.test_named_settle_keeps_dot_folders_but_empty_all_settle_cleans_without_a_launcher

# TEST-TIER-DISABLED-BEGIN tests/test_cleanup.py::Cleaning.test_failed_cleanup_is_reported_and_makes_all_settle_unsuccessful
#     def test_failed_cleanup_is_reported_and_makes_all_settle_unsuccessful(self) -> None:
#         """root.cleanup-failure"""
#         folder = self.dot(1, 'old')
#         with contextlib.redirect_stderr(io.StringIO()):
#             with mock.patch('arbol_root.cleanup.shutil.rmtree', side_effect=PermissionError('fixture')) as remove:
#                 remove.avoids_symlink_attacks = True
#                 self.assertEqual(settle(self.f.context).status, 1)
#         self.assertTrue(folder.is_dir())
# TEST-TIER-DISABLED-END tests/test_cleanup.py::Cleaning.test_failed_cleanup_is_reported_and_makes_all_settle_unsuccessful

# TEST-TIER-DISABLED-BEGIN tests/test_cleanup.py::Cleaning.test_cleanup_still_runs_before_a_no_fit_refusal
#     def test_cleanup_still_runs_before_a_no_fit_refusal(self) -> None:
#         folder = self.dot(1, 'old')
#         self.f.put(record(2))
#         with mock.patch('arbol_root.process.started_at', return_value=None):
#             with mock.patch('arbol_root.settle.chosen_build', side_effect=Refusal('no_fit','none')):
#                 with self.assertRaises(Refusal):
#                     settle(self.f.context)
#         self.assertFalse(folder.exists())
# TEST-TIER-DISABLED-END tests/test_cleanup.py::Cleaning.test_cleanup_still_runs_before_a_no_fit_refusal

# TEST-TIER-DISABLED-BEGIN tests/test_cleanup.py::Cleaning.test_disappeared_name_is_harmless_but_unavailable_catalogue_refuses
#     def test_disappeared_name_is_harmless_but_unavailable_catalogue_refuses(self) -> None:
#         """root.cleanup-disappearance"""
#         folder = self.dot(1, 'old')
#         original = shutil.rmtree
#         def gone(name: str, *, dir_fd: int) -> None:
#             original(name, dir_fd=dir_fd)
#             raise FileNotFoundError
#         with mock.patch('arbol_root.cleanup.shutil.rmtree', side_effect=gone) as remove:
#             remove.avoids_symlink_attacks = True
#             self.assertTrue(cleanup(self.f.context, now=1000))
#         self.assertFalse(folder.exists())
#         self.f.exchanges.rmdir()
#         self.assertTrue(cleanup(self.f.context))
#         self.f.exchanges.symlink_to(self.f.base, target_is_directory=True)
#         with self.assertRaises(Refusal) as error:
#             cleanup(self.f.context)
#         self.assertEqual(error.exception.code, 'root_unavailable')
# TEST-TIER-DISABLED-END tests/test_cleanup.py::Cleaning.test_disappeared_name_is_harmless_but_unavailable_catalogue_refuses


# Original deferred imports (restore at the required scope, never blindly at the tail).
# TEST-TIER-IMPORTS-BEGIN tests/test_cleanup.py:3
# import contextlib
# TEST-TIER-IMPORTS-END tests/test_cleanup.py:3

# TEST-TIER-IMPORTS-BEGIN tests/test_cleanup.py:4
# import io
# TEST-TIER-IMPORTS-END tests/test_cleanup.py:4

# TEST-TIER-IMPORTS-BEGIN tests/test_cleanup.py:5
# import json
# TEST-TIER-IMPORTS-END tests/test_cleanup.py:5

# TEST-TIER-IMPORTS-BEGIN tests/test_cleanup.py:7
# import shutil
# TEST-TIER-IMPORTS-END tests/test_cleanup.py:7

# TEST-TIER-IMPORTS-BEGIN tests/test_cleanup.py:10
# from datetime import UTC, datetime
# TEST-TIER-IMPORTS-END tests/test_cleanup.py:10

# TEST-TIER-IMPORTS-BEGIN tests/test_cleanup.py:12
# from unittest import mock
# TEST-TIER-IMPORTS-END tests/test_cleanup.py:12

# TEST-TIER-IMPORTS-BEGIN tests/test_cleanup.py:18
# from arbol_root.cleanup import cleanup  # noqa: E402
# TEST-TIER-IMPORTS-END tests/test_cleanup.py:18

# TEST-TIER-IMPORTS-BEGIN tests/test_cleanup.py:19
# from arbol_root.model import Refusal  # noqa: E402
# TEST-TIER-IMPORTS-END tests/test_cleanup.py:19

# TEST-TIER-IMPORTS-BEGIN tests/test_cleanup.py:20
# from arbol_root.settle import settle  # noqa: E402
# TEST-TIER-IMPORTS-END tests/test_cleanup.py:20

raise RuntimeError("Mid-tier tests require an explicitly requested testing task; see MID_TIER.md.")
