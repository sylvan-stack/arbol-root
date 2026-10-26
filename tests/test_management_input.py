from __future__ import annotations

import os
import signal
import subprocess
import sys
import tempfile
import time
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))
from arbol_root.input import parse  # noqa: E402
from arbol_root.model import Refusal  # noqa: E402

EXCHANGE = '7f3a2c1e-4b5d-4e6f-8a9b-0c1d2e3f4a5b'


class ManagementInput(unittest.TestCase):
    def test_stop_and_settle_uuid_arguments_and_common_options(self) -> None:
        """root.management-input"""
        self.assertEqual(parse(['settle']).exchange, None)
        for name in ['stop', 'settle']:
            command = parse(['--root=sapling', name, EXCHANGE, '--bin-dir', '/private-bin'])
            self.assertEqual((command.name, command.code, command.exchange), (name, None, EXCHANGE))
            self.assertEqual(command.options, {'--root':'sapling', '--bin-dir':'/private-bin'})
        self.assertEqual(parse(['stop', '--force', EXCHANGE]).options['--force'], 'true')
        self.assertEqual(parse(['stop', EXCHANGE, '--force']).exchange, EXCHANGE)

    def test_invalid_arguments_and_force_are_refused(self) -> None:
        for args in [['stop'], ['stop', 'bad'], ['settle', '../escape'], ['stop', EXCHANGE, EXCHANGE],
                     ['settle', EXCHANGE, EXCHANGE], ['--force', 'stop', EXCHANGE],
                     ['stop', '--force=true', EXCHANGE], ['stop', '--force', '--force', EXCHANGE],
                     ['settle', '--force', EXCHANGE], ['list', '--force'], ['stop', '-v', 'a', EXCHANGE]]:
            with self.subTest(args=args), self.assertRaises(Refusal) as error:
                parse(args)
            self.assertEqual(error.exception.code, 'invalid_input')


class ProcessFixture(unittest.TestCase):
    def test_private_leader_and_ignored_child_share_an_isolated_group(self) -> None:
        """root.stop-fixture"""
        program = Path(__file__).with_name('exchange_process.py')
        for mode in ['term', 'child', 'ignore']:
            with self.subTest(mode=mode), tempfile.TemporaryDirectory(prefix='root-group-fixture-') as temporary:
                folder = Path(temporary)
                process = subprocess.Popen([sys.executable, '-I', '-B', str(program), str(folder), mode],
                                           start_new_session=True, stdin=subprocess.DEVNULL,
                                           stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                try:
                    deadline = time.monotonic()+5
                    while not (folder / 'ready').exists():
                        self.assertIsNone(process.poll())
                        self.assertLess(time.monotonic(), deadline)
                        time.sleep(0.01)
                    self.assertEqual(os.getpgid(process.pid), process.pid)
                    self.assertNotEqual(process.pid, os.getpgrp())
                    if mode != 'term':
                        child = int((folder / 'child-pid').read_text())
                        self.assertEqual(os.getpgid(child), process.pid)
                    os.killpg(process.pid, signal.SIGTERM)
                    if mode == 'ignore':
                        time.sleep(0.05)
                        self.assertIsNone(process.poll())
                    else:
                        self.assertEqual(process.wait(timeout=5), -signal.SIGTERM)
                    if mode == 'child':
                        self.assertEqual(os.getpgid(child), process.pid)
                finally:
                    try:
                        os.killpg(process.pid, signal.SIGKILL)
                    except ProcessLookupError:
                        pass
                    process.wait(timeout=5)
