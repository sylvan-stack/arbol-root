"""Mid-tier selections. Write or run only in an explicitly requested testing task."""
from __future__ import annotations

import test_chat_migration as _support


class ChatModes(_support.ChatModes):


# TEST-TIER-BEGIN tests/test_chat_migration.py::ChatModes.test_failure_after_target_deletion_or_stale_update_rolls_back_all_rows
    def test_failure_after_target_deletion_or_stale_update_rolls_back_all_rows(self) -> None:
        """root.migration-chat-rollback"""
        import uuid

        from scripts.chat_migration_check import history, invoke
        from scripts.migration_fixtures import CHATS, EXCHANGES, seed
        inputs = self.inputs()
        source,target = 'rollback_source_'+uuid.uuid4().hex,'rollback_target_'+uuid.uuid4().hex
        for database in [source,target]:
            self.lab.server.createdb(database)
            self.lab.run_file(database,inputs.file('chat-tables.sql'))
        self.lab.run_file(target,inputs.file('root-tables.sql'))
        self.lab.run_file(source,inputs.folder/'roots/sapling/layout.sql')
        seed(self.lab.server,source)
        self.assertEqual(invoke(self.lab,inputs,source,target,'whole').returncode,0)
        self.lab.server.execute(source,f"UPDATE exchanges SET state='completed',ended_at=clock_timestamp() WHERE id='{EXCHANGES[2]}'")
        before,original = history(self.lab,target),history(self.lab,source)
        script = inputs.file('migrate.sql')
        sql = script.read_text()
        for mode,marker in [('chat','DELETE FROM exchanges WHERE chat_id=requested;'),
                            ('check','FROM source_progress s WHERE m.from_chat=s.chat_id AND m.from_root=current_setting(\'arbol.from_root\');')]:
            self.assertIn(marker,sql)
            script.write_text(sql.replace(marker,marker+'\n  PERFORM 1/0;'))
            result = invoke(self.lab,inputs,source,target,mode,CHATS[0])
            self.assertEqual(result.returncode,3,result.stderr)
            self.assertIn('division by zero',result.stderr)
            self.assertEqual(history(self.lab,target),before)
            self.assertEqual(history(self.lab,source),original)
# TEST-TIER-END tests/test_chat_migration.py::ChatModes.test_failure_after_target_deletion_or_stale_update_rolls_back_all_rows
