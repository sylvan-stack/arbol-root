"""Mid-tier selections. Write or run only in an explicitly requested testing task."""
from __future__ import annotations

import test_migration_drills as _support
from test_migration_drills import (CHATS ,Command ,EXCHANGES ,Path ,Snapshot ,SourceLock ,fingerprints ,frozen ,json ,processes ,stopped ,tempfile ,thaw_client ,threading ,wait_for)


class MigrationHelpers(_support.MigrationHelpers):

# TEST-TIER-BEGIN tests/test_migration_drills.py::MigrationHelpers.test_a_concurrent_transaction_never_splits_the_multi_table_snapshot
    def test_a_concurrent_transaction_never_splits_the_multi_table_snapshot(self) -> None:
        """sapling.migration-snapshot-consistency"""
        i = self.database('concurrent')
        self.lab.server.execute('concurrent',f"UPDATE chats SET title='v0' WHERE id='{CHATS[0]}'; "
            f"UPDATE messages SET text='v0' WHERE exchange_id='{EXCHANGES[0]}' AND position=0")
        ended = threading.Event()
        errors: list[BaseException] = []
        def writer() -> None:
            try:
                for number in range(12):
                    self.lab.server.execute('concurrent',f"UPDATE chats SET title='v{number}' "
                        f"WHERE id='{CHATS[0]}'; UPDATE messages SET text='v{number}' "
                        f"WHERE exchange_id='{EXCHANGES[0]}' AND position=0;")
                    if ended.wait(0.01):
                        break
            except BaseException as error:
                errors.append(error)
        thread = threading.Thread(target=writer)
        thread.start()
        try:
            for _ in range(6):
                value = Snapshot(i).read()['tables']
                title = next(x['title'] for x in value['chats']['rows'] if x['id'] == CHATS[0])
                message = next(x['text'] for x in value['messages']['rows']
                               if x['exchange_id'] == EXCHANGES[0] and x['position'] == 0)
                self.assertEqual(title,message)
        finally:
            ended.set()
            thread.join(timeout=10)
        self.assertFalse(thread.is_alive())
        self.assertEqual(errors,[])
# TEST-TIER-END tests/test_migration_drills.py::MigrationHelpers.test_a_concurrent_transaction_never_splits_the_multi_table_snapshot


# TEST-TIER-BEGIN tests/test_migration_drills.py::MigrationHelpers.test_frozen_source_copy_fails_after_private_shutdown_and_service_is_restored
    def test_frozen_source_copy_fails_after_private_shutdown_and_service_is_restored(self) -> None:
        """sapling.migration-private-outage"""
        i = self.database('privateoutage')
        before = fingerprints(Snapshot(i).read())
        with tempfile.TemporaryDirectory(prefix='private frozen migration ') as directory:
            home = Path(directory)
            frame = self.private_command(i,home)
            lock = SourceLock(i,home)
            command = Command(frame,['migrate','fictional'],'migration')
            try:
                wait_for(lock.blocked_copy,seconds=10,interval=0.1)
                child = wait_for(command.psql,seconds=5)
                with frozen(child,home/'freeze.json'):
                    with stopped(stop=self.lab.server.stop,restore=self.lab.server.start,
                                 healthy=self.lab.server.running,receipt=home/'restoration.json'):
                        thaw_client(child)
                        result = command.finish(status=1,seconds=10)
                        self.assertEqual(result['reply'],{'refused':True})
                self.assertTrue(json.loads((home/'restoration.json').read_text())['restored'])
                self.assertNotEqual(processes().get(child['pid']),child)
            finally:
                command.close()
                lock.close()
                if not self.lab.server.running():
                    self.lab.server.start()
            self.assertEqual(fingerprints(Snapshot(i).read()),before)
# TEST-TIER-END tests/test_migration_drills.py::MigrationHelpers.test_frozen_source_copy_fails_after_private_shutdown_and_service_is_restored
