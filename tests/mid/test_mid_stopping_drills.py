"""Commented mid-tier selections; see MID_TIER.md before restoring a case."""

# Restore the needed imports and class header only for an explicit testing task.
# import test_stopping_drills as _support
# from test_stopping_drills import (
#     Freeze,
#     IgnoredChild,
#     Path,
#     ROOT,
#     StoppingJudgment,
#     sys,
#     unittest,
# )


# class Freeze(_support.Freeze):
# TEST-TIER-DISABLED-BEGIN tests/test_stopping_drills.py::Freeze.test_a_private_process_is_thawed_after_success_body_failure_and_real_signals
#     def test_a_private_process_is_thawed_after_success_body_failure_and_real_signals(self) -> None:
#         """sapling.freeze-cleanup"""
#         with tempfile.TemporaryDirectory(prefix='private freeze ') as directory:
#             child = subprocess.Popen(['/bin/sleep','60'],start_new_session=True)
#             try:
#                 identity = processes()[child.pid]
#                 handlers = {n:signal.getsignal(n) for n in (signal.SIGINT,signal.SIGTERM)}
#                 for kind in ['success','failure','SIGINT','SIGTERM']:
#                     receipt = Path(directory)/(kind+'.json')
#                     try:
#                         with frozen(identity,receipt):
#                             state = subprocess.check_output(['/bin/ps','-o','stat=','-p',str(child.pid)],text=True)
#                             self.assertIn('T',state)
#                             if kind == 'failure':
#                                 raise ValueError('private failure')
#                             if kind.startswith('SIG'):
#                                 os.kill(os.getpid(),getattr(signal,kind))
#                     except (KeyboardInterrupt,ValueError):
#                         self.assertNotEqual(kind,'success')
#                     self.assertTrue(json.loads(receipt.read_text())['thawed'])
#                     self.assertNotIn('T',subprocess.check_output(['/bin/ps','-o','stat=','-p',str(child.pid)],text=True))
#                     self.assertEqual({n:signal.getsignal(n) for n in handlers},handlers)
#             finally:
#                 os.kill(child.pid,signal.SIGCONT)
#                 child.terminate()
#                 child.wait(timeout=5)
# TEST-TIER-DISABLED-END tests/test_stopping_drills.py::Freeze.test_a_private_process_is_thawed_after_success_body_failure_and_real_signals

# TEST-TIER-DISABLED-BEGIN tests/test_stopping_drills.py::Freeze.test_reused_or_stale_identity_never_gets_a_thaw_signal
#     def test_reused_or_stale_identity_never_gets_a_thaw_signal(self) -> None:
#         """sapling.freeze-reused-pid"""
#         with tempfile.TemporaryDirectory() as directory:
#             identity = {'pid':987654,'group':987654,'started':processes()[os.getpid()]['started']}
#             changed = {**identity,'started':identity['started']+timedelta(days=1)}
#             with mock.patch('stopping_support.processes',side_effect=[{987654:identity},{987654:changed}]),\
#                     mock.patch('stopping_support.os.kill') as kill:
#                 with frozen(identity,Path(directory)/'reused.json'):
#                     pass
#                 kill.assert_called_once_with(987654,signal.SIGSTOP)
#             with mock.patch('stopping_support.processes',return_value={987654:changed}),\
#                     mock.patch('stopping_support.os.kill') as kill:
#                 with self.assertRaises(DrillError):
#                     with frozen(identity,Path(directory)/'stale.json'):
#                         pass
#                 kill.assert_not_called()
# TEST-TIER-DISABLED-END tests/test_stopping_drills.py::Freeze.test_reused_or_stale_identity_never_gets_a_thaw_signal

# TEST-TIER-DISABLED-BEGIN tests/test_stopping_drills.py::Freeze.test_failure_during_stop_delivery_still_attempts_to_thaw_the_same_owned_process
#     def test_failure_during_stop_delivery_still_attempts_to_thaw_the_same_owned_process(self) -> None:
#         """sapling.freeze-delivery-race"""
#         with tempfile.TemporaryDirectory() as directory:
#             identity = {'pid':987654,'group':987654,'started':processes()[os.getpid()]['started']}
#             def deliver(pid: int, number: int) -> None:
#                 if number == signal.SIGSTOP:
#                     raise KeyboardInterrupt('arrived just after stop delivery')
#             with mock.patch('stopping_support.processes',return_value={987654:identity}),\
#                     mock.patch('stopping_support.os.kill',side_effect=deliver) as kill:
#                 with self.assertRaises(KeyboardInterrupt):
#                     with frozen(identity,Path(directory)/'race.json'):
#                         pass
#                 self.assertEqual([x.args for x in kill.call_args_list],
#                                  [(987654,signal.SIGSTOP),(987654,signal.SIGCONT)])
# TEST-TIER-DISABLED-END tests/test_stopping_drills.py::Freeze.test_failure_during_stop_delivery_still_attempts_to_thaw_the_same_owned_process



# class IgnoredChild(_support.IgnoredChild):
# TEST-TIER-DISABLED-BEGIN tests/test_stopping_drills.py::IgnoredChild.test_private_wrapper_child_records_term_and_survives_until_explicit_kill
#     def test_private_wrapper_child_records_term_and_survives_until_explicit_kill(self) -> None:
#         """sapling.force-child"""
#         with tempfile.TemporaryDirectory(prefix='private stopping wrapper ') as directory:
#             home = Path(directory)
#             launcher = home/'trunk'
#             launcher.write_text('#!/bin/sh\nexit 0\n')
#             launcher.chmod(0o700)
#             fixture = StandinHome(launcher,'selftest hold')
#             process: subprocess.Popen[str] | None = None
#             pid: int | None = None
#             try:
#                 exchange = mock.Mock()
#                 exchange.fixture = fixture
#                 ignored_child(exchange)
#                 request = home/'request.json'
#                 request.write_text(json.dumps({'input':'hold','runId':'private-stop','model':'standin-model'}))
#                 process = subprocess.Popen([str(fixture.bin/'arbol-claude-driver'),'run','--request',str(request)],
#                                            stdin=subprocess.DEVNULL,stdout=subprocess.DEVNULL,stderr=subprocess.PIPE,
#                                            text=True,start_new_session=True)
#                 file = fixture.home/'standin/ignored-child.json'
#                 value = wait_for(lambda:json.loads(file.read_text()) if file.exists() else None,seconds=10)
#                 pid = value['pid']
#                 self.assertEqual(os.getpgid(pid),process.pid)
#                 self.assertIn(pid,fixture.children())
#                 os.kill(pid,signal.SIGTERM)
#                 marker = fixture.home/'standin/ignored-signals.jsonl'
#                 wait_for(lambda:True if marker.exists() else None,seconds=5)
#                 self.assertEqual(json.loads(marker.read_text().splitlines()[0])['signal'],signal.SIGTERM)
#                 time.sleep(0.05)
#                 self.assertIn(pid,processes())
#             finally:
#                 if process is not None:
#                     os.killpg(process.pid,signal.SIGKILL)
#                     process.communicate(timeout=5)
#                 if pid is not None:
#                     wait_for(lambda:True if pid not in processes() else None,seconds=5)
#                 fixture.close()
# TEST-TIER-DISABLED-END tests/test_stopping_drills.py::IgnoredChild.test_private_wrapper_child_records_term_and_survives_until_explicit_kill

# TEST-TIER-DISABLED-BEGIN tests/test_stopping_drills.py::IgnoredChild.test_owned_manager_reply_and_kill_reap_only_the_started_private_command
#     def test_owned_manager_reply_and_kill_reap_only_the_started_private_command(self) -> None:
#         """sapling.owned-manager"""
#         with tempfile.TemporaryDirectory(prefix='private manager command ') as directory:
#             home = Path(directory)
#             (home/'bin').mkdir()
#             (home/'work').mkdir()
#             executable = home/'bin/arbol-root'
#             script = home/'private manager.py'
#             script.write_text('import json,sys,time\n'
#                               'if sys.argv[-1] == "wait": time.sleep(30)\n'
#                               'else: print(json.dumps({"root":"sapling","private":True}))\n')
#             # Packaged CPython itself lives beneath "Application Support"; never put it in a shebang.
#             executable.write_text('#!/bin/sh\nexec '+shlex.join([os.path.realpath(sys.executable),'-IB',str(script)])
#                                   +' "$@"\n')
#             executable.chmod(0o700)
#             frame = mock.Mock()
#             frame.places.home,frame.places.bin,frame.work,frame.evidence = home,home/'bin',home/'work',home
#             manager = Manager(frame,['reply'],'reply')
#             try:
#                 self.assertEqual(manager.finish()['reply'],{'root':'sapling','private':True})
#             finally:
#                 manager.close()
#             waiting = Manager(frame,['wait'],'waiting')
#             try:
#                 self.assertIsNone(waiting.process.poll())
#                 waiting.kill()
#                 self.assertEqual(waiting.process.returncode,-signal.SIGKILL)
#                 self.assertNotIn(waiting.process.pid,processes())
#             finally:
#                 waiting.close()
# TEST-TIER-DISABLED-END tests/test_stopping_drills.py::IgnoredChild.test_owned_manager_reply_and_kill_reap_only_the_started_private_command



# class StoppingJudgment(_support.StoppingJudgment):
# TEST-TIER-DISABLED-BEGIN tests/test_stopping_drills.py::StoppingJudgment.test_saved_graceful_reply_is_valid_but_force_and_settling_cannot_be_invented
#     def test_saved_graceful_reply_is_valid_but_force_and_settling_cannot_be_invented(self) -> None:
#         """sapling.stop-reply-judgment"""
#         stop_state({'reply':{'ended':'saved','forced':False}},'cancelled',forced=False)
#         stop_state({'reply':{'ended':'interrupted','forced':True,'settling':{'settled':'interrupted'}}},
#                    'interrupted',forced=True)
#         for reply in [{'ended':'none','forced':False},{'ended':'interrupted','forced':False},
#                       {'ended':'interrupted','forced':True}]:
#             with self.subTest(reply=reply),self.assertRaises(DrillError):
#                 stop_state({'reply':reply},'interrupted',forced=True)
# TEST-TIER-DISABLED-END tests/test_stopping_drills.py::StoppingJudgment.test_saved_graceful_reply_is_valid_but_force_and_settling_cannot_be_invented

# TEST-TIER-DISABLED-BEGIN tests/test_stopping_drills.py::StoppingJudgment.test_reuse_requires_retained_passing_checks_source_status_and_chosen_build
#     def test_reuse_requires_retained_passing_checks_source_status_and_chosen_build(self) -> None:
#         """sapling.newer-build-receipt"""
#         with tempfile.TemporaryDirectory() as directory:
#             home = Path(directory)
#             evidence = home/'evidence'
#             journal = evidence/'stopping-drills/newer-build-receipts.jsonl'
#             journal.parent.mkdir(parents=True)
#             checks = [{'name':name,'passed':True} for name in ['unit','layout','migration']]
#             source = {'commit':'verified','branch':'main','uncommittedChanges':False}
#             record = {'component':'arbol-root','build':'2','status':'working','root':'sapling',
#                       'source':source,'checks':checks}
#             folder = home/'Library/Application Support/Arbol/builds/arbol-root/2'
#             folder.mkdir(parents=True)
#             file = folder/'build.json'
#             file.write_text(json.dumps(record))
#             report = evidence/'report.json'
#             report.write_text(json.dumps({'passed':True,'check':'sapling.newer-build','newRootBuild':'2',
#                                           'built':{'source':source,'checks':checks}}))
#             journal.write_text(json.dumps({'report':str(report)})+'\n')
#             frame = mock.Mock()
#             frame.places.home,frame.places.evidence = home,evidence
#             frame.calls.run.return_value = {'rootBuild':'2'}
#             self.assertTrue(reuse_build(frame)['reusedQualifiedBuild'])
#             for changed in [{**record,'status':'failed'},{**record,'checks':[]},
#                             {**record,'source':{'commit':'changed'}}]:
#                 file.write_text(json.dumps(changed))
#                 with self.subTest(changed=changed),self.assertRaises(DrillError):
#                     reuse_build(frame)
#             file.write_text(json.dumps(record))
#             frame.calls.run.return_value = {'rootBuild':'3'}
#             with self.assertRaises(DrillError):
#                 reuse_build(frame)
# TEST-TIER-DISABLED-END tests/test_stopping_drills.py::StoppingJudgment.test_reuse_requires_retained_passing_checks_source_status_and_chosen_build


# Original deferred imports (restore at the required scope, never blindly at the tail).
# TEST-TIER-IMPORTS-BEGIN tests/test_stopping_drills.py:5
# import json
# TEST-TIER-IMPORTS-END tests/test_stopping_drills.py:5

# TEST-TIER-IMPORTS-BEGIN tests/test_stopping_drills.py:6
# import os
# TEST-TIER-IMPORTS-END tests/test_stopping_drills.py:6

# TEST-TIER-IMPORTS-BEGIN tests/test_stopping_drills.py:7
# import shlex
# TEST-TIER-IMPORTS-END tests/test_stopping_drills.py:7

# TEST-TIER-IMPORTS-BEGIN tests/test_stopping_drills.py:8
# import signal
# TEST-TIER-IMPORTS-END tests/test_stopping_drills.py:8

# TEST-TIER-IMPORTS-BEGIN tests/test_stopping_drills.py:9
# import subprocess
# TEST-TIER-IMPORTS-END tests/test_stopping_drills.py:9

# TEST-TIER-IMPORTS-BEGIN tests/test_stopping_drills.py:11
# import tempfile
# TEST-TIER-IMPORTS-END tests/test_stopping_drills.py:11

# TEST-TIER-IMPORTS-BEGIN tests/test_stopping_drills.py:12
# import time
# TEST-TIER-IMPORTS-END tests/test_stopping_drills.py:12

# TEST-TIER-IMPORTS-BEGIN tests/test_stopping_drills.py:14
# from datetime import timedelta
# TEST-TIER-IMPORTS-END tests/test_stopping_drills.py:14

# TEST-TIER-IMPORTS-BEGIN tests/test_stopping_drills.py:16
# from unittest import mock
# TEST-TIER-IMPORTS-END tests/test_stopping_drills.py:16

# TEST-TIER-IMPORTS-BEGIN tests/test_stopping_drills.py:20
# from drill_support import DrillError, wait_for  # noqa: E402
# TEST-TIER-IMPORTS-END tests/test_stopping_drills.py:20

# TEST-TIER-IMPORTS-BEGIN tests/test_stopping_drills.py:21
# from stopping_drills import reuse_build  # noqa: E402
# TEST-TIER-IMPORTS-END tests/test_stopping_drills.py:21

# TEST-TIER-IMPORTS-BEGIN tests/test_stopping_drills.py:22
# from stopping_support import Manager, frozen, ignored_child, stop_state  # noqa: E402
# TEST-TIER-IMPORTS-END tests/test_stopping_drills.py:22

# TEST-TIER-IMPORTS-BEGIN tests/test_stopping_drills.py:23
# from trunk_drill_support import StandinHome, processes  # noqa: E402
# TEST-TIER-IMPORTS-END tests/test_stopping_drills.py:23

raise RuntimeError("Mid-tier tests require an explicitly requested testing task; see MID_TIER.md.")
