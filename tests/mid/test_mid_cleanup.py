"""Mid-tier selections. Write or run only in an explicitly requested testing task."""
from __future__ import annotations

import test_cleanup as _support
from test_cleanup import (cleanup ,record)


class Cleaning(_support.Cleaning):


# TEST-TIER-BEGIN tests/test_cleanup.py::Cleaning.test_symlink_and_non_uuid_names_cannot_remove_an_outside_folder
    def test_symlink_and_non_uuid_names_cannot_remove_an_outside_folder(self) -> None:
        """root.cleanup-paths"""
        outside = self.f.base / 'outside'
        outside.mkdir()
        (outside / 'untouched').write_text('private fixture')
        link = self.f.exchanges / ('.'+record(1)['exchange']+'.old')
        link.symlink_to(outside, target_is_directory=True)
        other = self.f.exchanges / '.not-a-uuid.old'
        other.mkdir()
        self.assertTrue(cleanup(self.f.context, now=1000))
        self.assertEqual((outside / 'untouched').read_text(), 'private fixture')
        self.assertTrue(link.is_symlink())
        self.assertTrue(other.is_dir())
# TEST-TIER-END tests/test_cleanup.py::Cleaning.test_symlink_and_non_uuid_names_cannot_remove_an_outside_folder
