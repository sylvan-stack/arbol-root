# Shared fixtures only; test bodies are in top/ and mid/. See TESTS.md.
from __future__ import annotations

import contextlib
import signal
import sys
import unittest
from datetime import UTC, datetime, timedelta
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))
from management_support import Fixture  # noqa: E402
from test_listing import record  # noqa: E402
from test_stop import MovingClock  # noqa: E402

from arbol_root.groups import force_group, members  # noqa: E402
from arbol_root.model import Refusal  # noqa: E402

AT = datetime(2026,10,26,9,tzinfo=UTC)
PROCESS = {'pid':50,'startedAt':AT.isoformat()}


class GroupIdentity(unittest.TestCase):
    def simulated(self) -> contextlib.ExitStack:
        stack = contextlib.ExitStack()
        stack.enter_context(mock.patch('arbol_root.groups.process_alive', return_value=True))
        stack.enter_context(mock.patch('arbol_root.groups.os.getpgid', return_value=50))
        stack.enter_context(mock.patch('arbol_root.groups.os.getpgrp', return_value=99999))
        return stack


class NativeForce(unittest.TestCase):
    def setUp(self) -> None:
        self.f = Fixture(self)

    def check_mode(self, mode: str, expected: int) -> None:
        value = record(1)
        folder, child = self.f.live(value, mode)
        reply = self.f.cli('stop','--force',value['exchange'])
        self.assertEqual(reply.returncode, 0, reply.stderr)
        import json
        result = json.loads(reply.stdout)
        self.assertEqual((result['ended'],result['forced']), ('interrupted',True))
        self.assertEqual(result['settling'], {'exchange':value['exchange'],'settled':'interrupted'})
        self.assertEqual((folder / 'control').read_bytes(), b'')
        self.assertEqual(child.wait(timeout=5), -expected)
        self.assertEqual(members(child.pid), {})


# Archived complete imports; restore needed names in their original scope, not at this file tail.
