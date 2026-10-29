"""Mid-tier selections. Write or run only in an explicitly requested testing task."""
from __future__ import annotations

import test_sapling_drills as _support
from test_sapling_drills import (Budget ,Commands ,DirectoryWatch ,DrillError ,Inspector ,Installed ,Path ,Places ,ROOT ,Server ,json ,mock ,new_json ,os ,shlex ,signal ,stopped ,subprocess ,sys ,tempfile ,uuid)


class Outage(_support.Outage):
# TEST-TIER-BEGIN tests/test_sapling_drills.py::Outage.test_installed_stop_completes_smart_shutdown_with_an_established_private_connection
    def test_installed_stop_completes_smart_shutdown_with_an_established_private_connection(self) -> None:
        """sapling.connected-shutdown: refusing new clients alone is not a database outage."""
        with tempfile.TemporaryDirectory(prefix='sapling private connected outage ') as temporary:
            home = Path(temporary).resolve()
            server = Server.create(home/'postgres',home=home)
            client = subprocess.Popen([server.tools['psql'],'--no-psqlrc','--quiet','--no-align',
                                       '--tuples-only','--dbname',server.url('postgres')],
                                      stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE,
                                      text=True)
            try:
                assert client.stdin is not None and client.stdout is not None
                client.stdin.write('SELECT 1;\n')
                client.stdin.flush()
                self.assertEqual(client.stdout.readline().strip(),'1')
                service = Installed.__new__(Installed)
                service.places = Places(home,home/'bin',home/'evidence')
                service.data,service.pg_ctl,service.service = server.data,server.tools['pg_ctl'],'private-service'

                def bootout(*args: str) -> subprocess.CompletedProcess[str]:
                    self.assertEqual(args,('bootout','private-service'))
                    pid = server.postmaster_pid()
                    assert pid is not None and client.stdin is not None and client.stdout is not None
                    os.kill(pid,signal.SIGTERM)
                    # Smart shutdown leaves this already-established connection usable.
                    client.stdin.write('SELECT 2;\n')
                    client.stdin.flush()
                    self.assertEqual(client.stdout.readline().strip(),'2')
                    return subprocess.CompletedProcess(args,0,'','')

                with mock.patch.object(service,'command',side_effect=bootout),\
                        mock.patch.object(service,'healthy',side_effect=server.running):
                    service.stop()
                self.assertFalse(server.running())
                self.assertFalse((server.data/'postmaster.pid').exists())
                output,_diagnostics = client.communicate('SELECT 3;\n',timeout=5)
                self.assertNotEqual(client.returncode,0)
                self.assertNotIn('3',output.splitlines())
                server.start()
                self.assertIs(server.value('postgres','SELECT to_json(true)'),True)
            finally:
                if client.poll() is None:
                    client.kill()
                client.communicate(timeout=5)
                server.remove()
# TEST-TIER-END tests/test_sapling_drills.py::Outage.test_installed_stop_completes_smart_shutdown_with_an_established_private_connection

# TEST-TIER-BEGIN tests/test_sapling_drills.py::Outage.test_private_server_is_restored_after_success_failure_partial_stop_and_real_signals
    def test_private_server_is_restored_after_success_failure_partial_stop_and_real_signals(self) -> None:
        """sapling.restore: success, errors, partial stops and real SIGINT/SIGTERM all restore and prove health."""
        with tempfile.TemporaryDirectory(prefix='sapling private outage ') as temporary:
            home = Path(temporary).resolve()
            server = Server.create(home/'postgres',home=home)
            try:
                handlers = {number:signal.getsignal(number) for number in (signal.SIGINT,signal.SIGTERM)}
                def healthy() -> bool:
                    return server.running() and server.value('postgres','SELECT to_json(true)') is True

                for kind in ('success','failure','partial-stop','SIGINT','SIGTERM'):
                    with self.subTest(kind=kind):
                        receipt = home/(kind+'.json')
                        def stop(selected: str = kind) -> None:
                            server.stop()
                            if selected == 'partial-stop':
                                raise RuntimeError('failure after stopping')
                        try:
                            with stopped(stop=stop,restore=server.start,healthy=healthy,receipt=receipt):
                                self.assertFalse(server.running())
                                if kind == 'failure':
                                    raise RuntimeError('body failure')
                                if kind in ('SIGINT','SIGTERM'):
                                    os.kill(os.getpid(),getattr(signal,kind))
                        except (RuntimeError,KeyboardInterrupt):
                            self.assertNotEqual(kind,'success')
                        self.assertTrue(healthy())
                        self.assertTrue(json.loads(receipt.read_text())['restored'])
                        self.assertEqual({number:signal.getsignal(number) for number in handlers},handlers)
            finally:
                server.remove()
# TEST-TIER-END tests/test_sapling_drills.py::Outage.test_private_server_is_restored_after_success_failure_partial_stop_and_real_signals


# TEST-TIER-BEGIN tests/test_sapling_drills.py::Outage.test_run_directory_watch_detects_a_file_that_was_created_and_already_removed
    def test_run_directory_watch_detects_a_file_that_was_created_and_already_removed(self) -> None:
        """sapling.no-driver-run: two empty snapshots cannot hide a fleeting run file."""
        with tempfile.TemporaryDirectory() as temporary:
            folder = Path(temporary)
            watch = DirectoryWatch(folder)
            try:
                self.assertFalse(watch.changed())
                path = folder/'fictional-run.json'
                path.write_text('{}')
                path.unlink()
                self.assertEqual(list(folder.iterdir()),[])
                self.assertTrue(watch.changed())
            finally:
                watch.close()
# TEST-TIER-END tests/test_sapling_drills.py::Outage.test_run_directory_watch_detects_a_file_that_was_created_and_already_removed


class Frame(_support.Frame):

# TEST-TIER-BEGIN tests/test_sapling_drills.py::Frame.test_json_commands_preserve_arguments_and_reject_bad_status_or_non_json
    def test_json_commands_preserve_arguments_and_reject_bad_status_or_non_json(self) -> None:
        """sapling.commands"""
        program = self.places.bin/'reply'
        script = self.places.bin/'reply script.py'
        script.write_text('import json,sys\nprint(json.dumps(sys.argv[1:]))\n')
        interpreter = self.home/"packaged Python's directory"/'python'
        interpreter.parent.mkdir()
        interpreter.symlink_to(os.path.realpath(sys.executable))
        program.write_text('#!/bin/sh\nexec '+shlex.join([str(interpreter),'-I','-B',str(script)])+' "$@"\n')
        program.chmod(0o755)
        args = ['one two',"a'b",'$HOME','🌲']
        for login in (False,True):
            with self.subTest(login=login):
                self.assertEqual(Commands(self.places,login=login).run('reply',*args),args)
        program.write_text('#!/bin/sh\nprintf not-json\n')
        for login in (False,True):
            with self.subTest(login=login),self.assertRaises(DrillError):
                Commands(self.places,login=login).run('reply')
        program.write_text('#!/bin/sh\nexit 3\n')
        for login in (False,True):
            with self.subTest(login=login),self.assertRaisesRegex(DrillError,'returned 3'):
                Commands(self.places,login=login).run('reply')
# TEST-TIER-END tests/test_sapling_drills.py::Frame.test_json_commands_preserve_arguments_and_reject_bad_status_or_non_json


# TEST-TIER-BEGIN tests/test_sapling_drills.py::Frame.test_two_processes_cannot_both_spend_the_last_available_message
    def test_two_processes_cannot_both_spend_the_last_available_message(self) -> None:
        """sapling.budget-concurrent"""
        budget = Budget(self.places.evidence)
        for _ in range(9):
            budget.reserve(str(uuid.uuid4()))
        code = ("import sys;sys.path.insert(0,"+repr(str(ROOT/'roots/sapling/drills'))+")\n"
                "from drill_support import Budget,DrillError\nfrom pathlib import Path\n"
                "try: Budget(Path(sys.argv[1])).reserve(sys.argv[2])\n"
                "except DrillError: sys.exit(1)\n")
        children = [subprocess.Popen([sys.executable,'-I','-B','-c',code,str(self.places.evidence),str(uuid.uuid4())],
                                     stdout=subprocess.PIPE,stderr=subprocess.PIPE) for _ in range(2)]
        try:
            for child in children:
                child.communicate(timeout=5)
            self.assertEqual(sorted(child.returncode for child in children),[0,1])
            self.assertEqual(budget.status()['usedOrReserved'],10)
        finally:
            for child in children:
                if child.poll() is None:
                    child.kill()
                child.communicate(timeout=5)
# TEST-TIER-END tests/test_sapling_drills.py::Frame.test_two_processes_cannot_both_spend_the_last_available_message


class ReadOnly(_support.ReadOnly):
# TEST-TIER-BEGIN tests/test_sapling_drills.py::ReadOnly.test_inspection_uses_its_private_server_and_cannot_write
    def test_inspection_uses_its_private_server_and_cannot_write(self) -> None:
        """sapling.read-only"""
        with tempfile.TemporaryDirectory(prefix='sapling inspector ') as temporary:
            home = Path(temporary).resolve()
            places = Places(home,home/'bin',home/'evidence')
            server = Server.create(home/'postgres',home=home)
            try:
                server.createdb('fictional')
                server.execute('fictional','CREATE TABLE notes(value integer); INSERT INTO notes VALUES (1); '
                               'CREATE SEQUENCE probe_seq;')
                root = places.roots/'sapling'
                root.mkdir(parents=True)
                new_json(root/'root.json',{'root':'sapling','rootContract':1,'database':'fictional'})
                new_json(home/'.arbol/database.json',{'address':server.address})
                security = home/'no-credential'
                security.write_text('#!/bin/sh\nexit 44\n')
                security.chmod(0o755)
                inspector = Inspector(places,psql=server.tools['psql'],security=str(security))
                self.assertEqual(inspector.read('SELECT json_agg(value) FROM notes'),[1])
                with self.assertRaises(DrillError):
                    inspector.read('DELETE FROM notes')
                with self.assertRaises(DrillError):
                    inspector.read('SELECT 1; DELETE FROM notes')
                with self.assertRaises(DrillError):
                    inspector.read("SELECT nextval('probe_seq')")
                self.assertFalse(server.value('fictional','SELECT to_json(is_called) FROM probe_seq'))
                self.assertEqual(server.value('fictional','SELECT count(*) FROM notes'),1)
                self.assertEqual(set(inspector.environment),{'HOME','PATH','LANG'})
            finally:
                server.remove()
# TEST-TIER-END tests/test_sapling_drills.py::ReadOnly.test_inspection_uses_its_private_server_and_cannot_write
