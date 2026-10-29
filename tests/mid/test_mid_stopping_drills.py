"""Mid-tier selections. Write or run only in an explicitly requested testing task."""
from __future__ import annotations

import test_stopping_drills as _support
from test_stopping_drills import (Path ,frozen ,json ,mock ,os ,processes ,signal ,subprocess ,tempfile)


class Freeze(_support.Freeze):
# TEST-TIER-BEGIN tests/test_stopping_drills.py::Freeze.test_a_private_process_is_thawed_after_success_body_failure_and_real_signals
    def test_a_private_process_is_thawed_after_success_body_failure_and_real_signals(self) -> None:
        """sapling.freeze-cleanup"""
        with tempfile.TemporaryDirectory(prefix='private freeze ') as directory:
            child = subprocess.Popen(['/bin/sleep','60'],start_new_session=True)
            try:
                identity = processes()[child.pid]
                handlers = {n:signal.getsignal(n) for n in (signal.SIGINT,signal.SIGTERM)}
                for kind in ['success','failure','SIGINT','SIGTERM']:
                    receipt = Path(directory)/(kind+'.json')
                    try:
                        with frozen(identity,receipt):
                            state = subprocess.check_output(['/bin/ps','-o','stat=','-p',str(child.pid)],text=True)
                            self.assertIn('T',state)
                            if kind == 'failure':
                                raise ValueError('private failure')
                            if kind.startswith('SIG'):
                                os.kill(os.getpid(),getattr(signal,kind))
                    except (KeyboardInterrupt,ValueError):
                        self.assertNotEqual(kind,'success')
                    self.assertTrue(json.loads(receipt.read_text())['thawed'])
                    self.assertNotIn('T',subprocess.check_output(['/bin/ps','-o','stat=','-p',str(child.pid)],text=True))
                    self.assertEqual({n:signal.getsignal(n) for n in handlers},handlers)
            finally:
                os.kill(child.pid,signal.SIGCONT)
                child.terminate()
                child.wait(timeout=5)
# TEST-TIER-END tests/test_stopping_drills.py::Freeze.test_a_private_process_is_thawed_after_success_body_failure_and_real_signals


# TEST-TIER-BEGIN tests/test_stopping_drills.py::Freeze.test_failure_during_stop_delivery_still_attempts_to_thaw_the_same_owned_process
    def test_failure_during_stop_delivery_still_attempts_to_thaw_the_same_owned_process(self) -> None:
        """sapling.freeze-delivery-race"""
        with tempfile.TemporaryDirectory() as directory:
            identity = {'pid':987654,'group':987654,'started':processes()[os.getpid()]['started']}
            def deliver(pid: int, number: int) -> None:
                if number == signal.SIGSTOP:
                    raise KeyboardInterrupt('arrived just after stop delivery')
            with mock.patch('stopping_support.processes',return_value={987654:identity}),\
                    mock.patch('stopping_support.os.kill',side_effect=deliver) as kill:
                with self.assertRaises(KeyboardInterrupt):
                    with frozen(identity,Path(directory)/'race.json'):
                        pass
                self.assertEqual([x.args for x in kill.call_args_list],
                                 [(987654,signal.SIGSTOP),(987654,signal.SIGCONT)])
# TEST-TIER-END tests/test_stopping_drills.py::Freeze.test_failure_during_stop_delivery_still_attempts_to_thaw_the_same_owned_process
