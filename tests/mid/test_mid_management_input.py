"""Mid-tier selections. Write or run only in an explicitly requested testing task."""
from __future__ import annotations

import test_management_input as _support
from test_management_input import (
    EXCHANGE,
    ManagementInput,
    Path,
    ProcessFixture,
    Refusal,
    os,
    parse,
    signal,
    subprocess,
    sys,
    tempfile,
    time,
    unittest,
)


class ManagementInput(_support.ManagementInput):
# TEST-TIER-BEGIN tests/test_management_input.py::ManagementInput.test_invalid_arguments_and_force_are_refused
    def test_invalid_arguments_and_force_are_refused(self) -> None:
        for args in [['stop'], ['stop', 'bad'], ['settle', '../escape'], ['stop', EXCHANGE, EXCHANGE],
                     ['settle', EXCHANGE, EXCHANGE], ['--force', 'stop', EXCHANGE],
                     ['stop', '--force=true', EXCHANGE], ['stop', '--force', '--force', EXCHANGE],
                     ['settle', '--force', EXCHANGE], ['list', '--force'], ['stop', '-v', 'a', EXCHANGE]]:
            with self.subTest(args=args), self.assertRaises(Refusal) as error:
                parse(args)
            self.assertEqual(error.exception.code, 'invalid_input')
# TEST-TIER-END tests/test_management_input.py::ManagementInput.test_invalid_arguments_and_force_are_refused



class ProcessFixture(_support.ProcessFixture):
# TEST-TIER-BEGIN tests/test_management_input.py::ProcessFixture.test_private_leader_and_ignored_child_share_an_isolated_group
    def test_private_leader_and_ignored_child_share_an_isolated_group(self) -> None:
        """root.stop-fixture"""
        program = Path(_support.__file__).with_name('exchange_process.py')
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
# TEST-TIER-END tests/test_management_input.py::ProcessFixture.test_private_leader_and_ignored_child_share_an_isolated_group
