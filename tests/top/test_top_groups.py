"""Individually selected top-tier cases. Shared fixtures retain their original paths."""
from __future__ import annotations

import test_groups as _support
from test_groups import (
    AT,
    MovingClock,
    PROCESS,
    Refusal,
    force_group,
    mock,
    signal,
    timedelta,
)


class GroupIdentity(_support.GroupIdentity):
    def test_reused_or_unanchored_group_is_never_killed_after_term(self) -> None:
        """root.stop-group-identity"""
        clock = MovingClock()
        for replacement in [{50:AT+timedelta(seconds=9)}, {51:AT}]:
            with self.subTest(replacement=replacement), self.simulated():
                with mock.patch('arbol_root.groups.members', side_effect=[{50:AT},replacement]):
                    with mock.patch('arbol_root.groups.os.killpg') as send:
                        with self.assertRaises(Refusal) as error:
                            force_group(PROCESS, clock.now, clock.pause)
            self.assertEqual(error.exception.code, 'not_ended')
            send.assert_called_once_with(50, signal.SIGTERM)
