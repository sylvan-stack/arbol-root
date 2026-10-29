"""Mid-tier selections. Write or run only in an explicitly requested testing task."""
from __future__ import annotations

import test_groups as _support
from test_groups import (signal)


class NativeForce(_support.NativeForce):


# TEST-TIER-BEGIN tests/test_groups.py::NativeForce.test_ignored_child_is_killed_after_its_leader_exits
    def test_ignored_child_is_killed_after_its_leader_exits(self) -> None:
        """root.stop-orphaned-child"""
        self.check_mode('child', signal.SIGTERM)
# TEST-TIER-END tests/test_groups.py::NativeForce.test_ignored_child_is_killed_after_its_leader_exits
