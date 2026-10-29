"""Mid-tier selections. Write or run only in an explicitly requested testing task."""
from __future__ import annotations

import test_migration_check as _support
from test_migration_check import (run_migration)


class MigrationCheck(_support.MigrationCheck):


# TEST-TIER-BEGIN tests/test_migration_check.py::MigrationCheck.test_corrupting_copied_text_fails_the_actual_row_judgment
    def test_corrupting_copied_text_fails_the_actual_row_judgment(self) -> None:
        """root.migration-text-fault"""
        inputs,older,_home = self.inputs()
        script = inputs.file('migrate.sql')
        text = script.read_text().rsplit('COMMIT;',1)
        script.write_text(text[0]+"\nUPDATE messages SET text='corrupted';\nCOMMIT;"+text[1])
        with self.assertRaisesRegex(ValueError,'exact text/JSON'):
            run_migration(inputs,self.lab,older)
# TEST-TIER-END tests/test_migration_check.py::MigrationCheck.test_corrupting_copied_text_fails_the_actual_row_judgment
