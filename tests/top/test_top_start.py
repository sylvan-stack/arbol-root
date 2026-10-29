"""Individually selected top-tier cases. Shared fixtures retain their original paths."""
from __future__ import annotations

import test_start as _support
from test_start import (
    Refusal,
    mock,
    parse,
    start,
)


class Starting(_support.Starting):
    def test_returns_on_a_fragmented_object_without_waiting_for_trunk_exit(self) -> None:
        """root.start-acceptance"""
        self.script(fragments=[{'text':'diagnostic\n[]\n{"accepted":','delay':0.02}, {'text':'true}\n'}],hold=True)
        with mock.patch('arbol_root.start.subprocess.Popen',side_effect=self.spawn):
            reply = start(self.context,parse(['start',*self.options,'-v','a']))
        self.assertEqual((reply.raw,reply.status), (b'{"accepted":true}\n',0))
        self.assertIsNone(self.children[-1].poll())
        (self.bin / 'release').touch()
        self.assertEqual(self.children[-1].wait(timeout=5), 0)

    def test_timeout_keeps_request_and_process_and_a_late_writer_can_still_finish(self) -> None:
        """root.start-timeout"""
        self.script(holdReply=True,hold=True)
        before = self.request.read_bytes()
        with mock.patch('arbol_root.start.subprocess.Popen',side_effect=self.spawn):
            with self.assertRaises(Refusal) as error:
                start(self.context,parse(['start',*self.options,'-v','a']),timeout=0.08)
        self.assertEqual(error.exception.code, 'no_answer')
        self.assertEqual(self.request.read_bytes(), before)
        self.assertIsNone(self.children[-1].poll())
        (self.bin / 'reply-release').touch()
        (self.bin / 'release').touch()
        self.assertEqual(self.children[-1].wait(timeout=5), 0)  # late write must not receive SIGPIPE/EPIPE
