"""Mid-tier selections. Write or run only in an explicitly requested testing task."""
from __future__ import annotations

import test_layout_compatibility as _support
from test_layout_compatibility import (OLD ,run_layout)


class LayoutCompatibility(_support.LayoutCompatibility):


# TEST-TIER-BEGIN tests/test_layout_compatibility.py::LayoutCompatibility.test_unique_index_and_new_check_on_an_older_table_are_refused
    def test_unique_index_and_new_check_on_an_older_table_are_refused(self) -> None:
        """root.layout-new-constraints"""
        for extra in ["CREATE UNIQUE INDEX IF NOT EXISTS notes_new_unique ON notes(id);",
                      "ALTER TABLE notes ADD CONSTRAINT must_be_positive CHECK(id>=0);"]:
            with self.subTest(extra=extra), self.assertRaises(ValueError):
                run_layout(self.inputs(OLD+extra),self.lab)
# TEST-TIER-END tests/test_layout_compatibility.py::LayoutCompatibility.test_unique_index_and_new_check_on_an_older_table_are_refused
