# Shared fixtures; case bodies live in top/ and mid/. See TESTS.md.
from __future__ import annotations
import subprocess
from types import SimpleNamespace


import contextlib
import signal
import sys
import unittest
from datetime import UTC, datetime, timedelta
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))
from arbol_root.groups import continuing, force_group, members  # noqa: E402
from arbol_root.model import Identity, Refusal  # noqa: E402
from arbol_root.stop import Observed, force_end, stop  # noqa: E402

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

# LOW TIER — DO NOT ENABLE OR RECREATE
# Historical examples only. Read before adding related tests; never execute.
# LOW-TIER-BEGIN: tests/test_groups.py::GroupIdentity.test_os_clock_is_uptime_raw_on_this_mac
# Reason: Mocks the clock and copies the wrapper exact clock-selection expression; it does not establish awake-time semantics.
# Source: arbol-root@6e90ef97197cad6753af59c46d4b4be5571b2025:tests/test_groups.py
# Retained evidence at review: Clock-jump/deadline and process ownership/termination cases remain; platform semantics are not inferred from this mock.
# Historical fixtures and class context are available at the source revision; no active dependencies restored.
# LOW-TIER-SOURCE-BEGIN
#     def test_os_clock_is_uptime_raw_on_this_mac(self) -> None:
#         """root.stop-awake-clock"""
#         import time
#         with mock.patch('arbol_root.clock.time.clock_gettime', return_value=123.5) as read:
#             self.assertEqual(awake(), 123.5)
#         read.assert_called_once_with(getattr(time,'CLOCK_UPTIME_RAW',time.CLOCK_MONOTONIC))
# LOW-TIER-SOURCE-END
# LOW-TIER-END
