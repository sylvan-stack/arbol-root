"""Mid-tier selections. Write or run only in an explicitly requested testing task."""
from __future__ import annotations

import test_layout_compatibility as _support
from test_layout_compatibility import (
    BuildInput,
    LayoutCompatibility,
    OLD,
    Path,
    ROOT,
    SqlLab,
    contextlib,
    earlier_build,
    json,
    private_server,
    run_layout,
    shutil,
    sys,
    tempfile,
    test_sql_support,
    unittest,
)


class LayoutCompatibility(_support.LayoutCompatibility):
# TEST-TIER-BEGIN tests/test_layout_compatibility.py::LayoutCompatibility.test_nullable_defaulted_columns_nonunique_index_and_new_table_are_compatible
    def test_nullable_defaulted_columns_nonunique_index_and_new_table_are_compatible(self) -> None:
        """root.layout-compatible-additions"""
        extra = """
ALTER TABLE notes ADD COLUMN IF NOT EXISTS title text;
COMMENT ON COLUMN notes.title IS 'Optional title';
ALTER TABLE notes ADD COLUMN IF NOT EXISTS pinned boolean NOT NULL DEFAULT false;
COMMENT ON COLUMN notes.pinned IS 'Defaulted flag';
CREATE INDEX IF NOT EXISTS notes_title ON notes(title);
CREATE TABLE IF NOT EXISTS extra(id integer PRIMARY KEY, parent integer REFERENCES notes(id), CHECK(id>=0));
COMMENT ON TABLE extra IS 'New table';
COMMENT ON COLUMN extra.id IS 'Identity';
COMMENT ON COLUMN extra.parent IS 'Parent';
"""
        inputs = self.inputs(OLD+extra)
        old = (inputs.folder.parent / '1/layout/root-tables.sql').read_bytes()
        report = run_layout(inputs,self.lab)
        self.assertEqual(report['earlierBuild'],'1')
        self.assertEqual((inputs.folder.parent / '1/layout/root-tables.sql').read_bytes(),old)
# TEST-TIER-END tests/test_layout_compatibility.py::LayoutCompatibility.test_nullable_defaulted_columns_nonunique_index_and_new_table_are_compatible

# TEST-TIER-BEGIN tests/test_layout_compatibility.py::LayoutCompatibility.test_editing_an_earlier_statement_is_refused
    def test_editing_an_earlier_statement_is_refused(self) -> None:
        """root.layout-edited-statement"""
        inputs = self.inputs(OLD.replace('id integer','id bigint'))
        with self.assertRaisesRegex(ValueError,'earlier Build'):
            run_layout(inputs,self.lab)
# TEST-TIER-END tests/test_layout_compatibility.py::LayoutCompatibility.test_editing_an_earlier_statement_is_refused

# TEST-TIER-BEGIN tests/test_layout_compatibility.py::LayoutCompatibility.test_required_column_without_default_is_refused_on_an_older_table
    def test_required_column_without_default_is_refused_on_an_older_table(self) -> None:
        """root.layout-required-column"""
        inputs = self.inputs(OLD+"ALTER TABLE notes ADD COLUMN IF NOT EXISTS required integer NOT NULL;"
                             "COMMENT ON COLUMN notes.required IS 'Required';")
        with self.assertRaisesRegex(ValueError,'NOT NULL'):
            run_layout(inputs,self.lab)
# TEST-TIER-END tests/test_layout_compatibility.py::LayoutCompatibility.test_required_column_without_default_is_refused_on_an_older_table

# TEST-TIER-BEGIN tests/test_layout_compatibility.py::LayoutCompatibility.test_unique_index_and_new_check_on_an_older_table_are_refused
    def test_unique_index_and_new_check_on_an_older_table_are_refused(self) -> None:
        """root.layout-new-constraints"""
        for extra in ["CREATE UNIQUE INDEX IF NOT EXISTS notes_new_unique ON notes(id);",
                      "ALTER TABLE notes ADD CONSTRAINT must_be_positive CHECK(id>=0);"]:
            with self.subTest(extra=extra), self.assertRaises(ValueError):
                run_layout(self.inputs(OLD+extra),self.lab)
# TEST-TIER-END tests/test_layout_compatibility.py::LayoutCompatibility.test_unique_index_and_new_check_on_an_older_table_are_refused

# TEST-TIER-BEGIN tests/test_layout_compatibility.py::LayoutCompatibility.test_appending_a_comment_override_cannot_change_an_older_object
    def test_appending_a_comment_override_cannot_change_an_older_object(self) -> None:
        inputs = self.inputs(OLD+"COMMENT ON TABLE notes IS 'Changed';")
        with self.assertRaisesRegex(ValueError,'older comments'):
            run_layout(inputs,self.lab)
# TEST-TIER-END tests/test_layout_compatibility.py::LayoutCompatibility.test_appending_a_comment_override_cannot_change_an_older_object

# TEST-TIER-BEGIN tests/test_layout_compatibility.py::LayoutCompatibility.test_statement_presentation_changes_preserve_the_same_schema
    def test_statement_presentation_changes_preserve_the_same_schema(self) -> None:
        inputs = self.inputs(OLD.replace('CREATE TABLE','create\n table')+'-- new prose comment\n')
        self.assertEqual(run_layout(inputs,self.lab)['earlierBuild'],'1')
# TEST-TIER-END tests/test_layout_compatibility.py::LayoutCompatibility.test_statement_presentation_changes_preserve_the_same_schema

# TEST-TIER-BEGIN tests/test_layout_compatibility.py::LayoutCompatibility.test_baseline_is_highest_earlier_matching_working_build_with_both_files
    def test_baseline_is_highest_earlier_matching_working_build_with_both_files(self) -> None:
        """root.layout-baseline"""
        inputs = self.inputs(OLD)
        base = inputs.folder.parent
        for number, patch in [('5',{}), ('6',{}), ('7',{'prunedAt':'2026-10-26T10:00:00Z'}),
                              ('8',{'status':'failed'}), ('9',{'root':'other'}), ('b',{})]:
            shutil.copytree(base / '1',base / number)
            record = json.loads((base / number / 'build.json').read_text())
            (base / number / 'build.json').write_text(json.dumps({**record,'build':number, **patch}))
        (base / '6/layout/chat-tables.sql').unlink()
        self.assertEqual(earlier_build(inputs),base / '5')
        (base / '5/build.json').write_text('{broken}')
        self.assertEqual(earlier_build(inputs),base / '1')
# TEST-TIER-END tests/test_layout_compatibility.py::LayoutCompatibility.test_baseline_is_highest_earlier_matching_working_build_with_both_files
