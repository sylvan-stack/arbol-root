"""Mid-tier selections. Write or run only in an explicitly requested testing task."""
from __future__ import annotations

import test_sql_support as _support
from test_sql_support import (ROOT ,mock ,os ,private_server)


class SqlSupport(_support.SqlSupport):


# TEST-TIER-BEGIN tests/test_sql_support.py::SqlSupport.test_private_server_ignores_caller_pg_variables_and_dumps_a_stable_schema
    def test_private_server_ignores_caller_pg_variables_and_dumps_a_stable_schema(self) -> None:
        """root.sql-private-server"""
        with mock.patch.dict(os.environ, {'PGHOST':'owner.invalid','PGOPTIONS':'invalid fixture option',
                                          'PGPASSWORD':'unused-fictional'}):
            with private_server() as lab:
                lab.server.createdb('fixture')
                lab.run_file('fixture', ROOT / 'contract/1/layout.sql')
                before = lab.dump('fixture')
                self.assertTrue(before)
                self.assertEqual(before, lab.dump('fixture'))
                self.assertEqual(set(lab.environment), {'HOME','PATH','LANG'})
                self.assertEqual(lab.server.value('fixture','SELECT to_json(inet_server_addr() IS NULL)'), True)
                socket, data, home = lab.server.socket_folder, lab.server.data, lab.server.home
                self.assertTrue(socket.is_dir())
        self.assertFalse(socket.exists())
        self.assertFalse(data.exists())
        self.assertFalse(home.exists())
# TEST-TIER-END tests/test_sql_support.py::SqlSupport.test_private_server_ignores_caller_pg_variables_and_dumps_a_stable_schema
