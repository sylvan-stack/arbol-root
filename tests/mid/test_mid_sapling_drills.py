"""Mid-tier selections. Write or run only in an explicitly requested testing task."""
from __future__ import annotations

import test_sapling_drills as _support
from test_sapling_drills import (
    Any,
    Budget,
    Commands,
    Creation,
    DirectoryWatch,
    DrillError,
    Frame,
    Inspector,
    Installed,
    MessageCommands,
    Messages,
    Outage,
    Path,
    Places,
    ROOT,
    ReadOnly,
    Server,
    json,
    judge,
    make_sapling,
    mock,
    new_json,
    os,
    real_messages,
    shlex,
    signal,
    stat,
    stopped,
    subprocess,
    sys,
    tempfile,
    time,
    unittest,
    uuid,
    wait_for,
)


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

# TEST-TIER-BEGIN tests/test_sapling_drills.py::Outage.test_failed_restore_is_reported_and_original_handlers_are_still_restored
    def test_failed_restore_is_reported_and_original_handlers_are_still_restored(self) -> None:
        """sapling.restore-failure: an unverified restoration cannot produce a passing receipt."""
        with tempfile.TemporaryDirectory() as temporary:
            receipt = Path(temporary)/'failed.json'
            state = [True]
            def stop() -> None:
                state[0] = False
            def restore() -> None:
                raise RuntimeError('private planted restore failure')
            handlers = {number:signal.getsignal(number) for number in (signal.SIGINT,signal.SIGTERM)}
            with self.assertRaisesRegex(DrillError,'restoration did not pass'):
                with stopped(stop=stop,restore=restore,healthy=lambda:state[0],receipt=receipt):
                    pass
            self.assertFalse(json.loads(receipt.read_text())['restored'])
            self.assertEqual({number:signal.getsignal(number) for number in handlers},handlers)
# TEST-TIER-END tests/test_sapling_drills.py::Outage.test_failed_restore_is_reported_and_original_handlers_are_still_restored

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
# TEST-TIER-BEGIN tests/test_sapling_drills.py::Frame.test_receipts_are_private_and_never_overwrite_an_earlier_attempt
    def test_receipts_are_private_and_never_overwrite_an_earlier_attempt(self) -> None:
        """sapling.receipt"""
        path = self.places.evidence/'request.json'
        new_json(path,{'message':'fictional 🌲'})
        self.assertEqual(stat.S_IMODE(path.stat().st_mode),0o600)
        with self.assertRaises(FileExistsError):
            new_json(path,{'message':'must not replace'})
        self.assertEqual(json.loads(path.read_text())['message'],'fictional 🌲')
# TEST-TIER-END tests/test_sapling_drills.py::Frame.test_receipts_are_private_and_never_overwrite_an_earlier_attempt

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

# TEST-TIER-BEGIN tests/test_sapling_drills.py::Frame.test_wait_has_a_deadline_and_never_retries_after_that_deadline
    def test_wait_has_a_deadline_and_never_retries_after_that_deadline(self) -> None:
        """sapling.wait"""
        moment = [0.0]
        calls = []
        def probe() -> None:
            calls.append(moment[0])
        def pause(delay: float) -> None:
            moment[0] += delay
        with self.assertRaises(DrillError):
            wait_for(probe,seconds=1,interval=0.3,clock=lambda:moment[0],pause=pause)
        self.assertEqual(moment[0],1)
        self.assertLessEqual(max(calls),1)
# TEST-TIER-END tests/test_sapling_drills.py::Frame.test_wait_has_a_deadline_and_never_retries_after_that_deadline

# TEST-TIER-BEGIN tests/test_sapling_drills.py::Frame.test_budget_reserves_before_submission_caps_ten_and_never_replays_an_exchange
    def test_budget_reserves_before_submission_caps_ten_and_never_replays_an_exchange(self) -> None:
        """sapling.budget"""
        budget = Budget(self.places.evidence)
        exchanges = [str(uuid.uuid4()) for _ in range(10)]
        for exchange in exchanges:
            budget.reserve(exchange)
        self.assertEqual(budget.status()['remaining'],0)
        with self.assertRaises(DrillError):
            budget.reserve(str(uuid.uuid4()))
        with self.assertRaises(DrillError):
            budget.reserve(exchanges[0])
        budget.finish(exchanges[0],'completed',usage={'costUSD':0.001})
        self.assertEqual(budget.status()['usedOrReserved'],10)
        with self.assertRaises(DrillError):
            budget.finish(exchanges[0],'no_vendor')
        budget.finish(exchanges[1],'no_vendor')
        budget.reserve(str(uuid.uuid4()),'SYL-187')
        self.assertEqual(budget.status()['remaining'],0)
# TEST-TIER-END tests/test_sapling_drills.py::Frame.test_budget_reserves_before_submission_caps_ten_and_never_replays_an_exchange

# TEST-TIER-BEGIN tests/test_sapling_drills.py::Frame.test_torn_or_unknown_budget_history_refuses_new_spending
    def test_torn_or_unknown_budget_history_refuses_new_spending(self) -> None:
        """sapling.budget-refusal"""
        folder = self.places.evidence
        folder.mkdir()
        journal = folder/'live-message-budget.jsonl'
        for content in ['{"version":1', '{"version":2}\n', 'not-json\n']:
            journal.write_text(content)
            with self.subTest(content=content),self.assertRaises(DrillError):
                Budget(folder).reserve(str(uuid.uuid4()))
# TEST-TIER-END tests/test_sapling_drills.py::Frame.test_torn_or_unknown_budget_history_refuses_new_spending

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



class Creation(_support.Creation):
# TEST-TIER-BEGIN tests/test_sapling_drills.py::Creation.test_creation_runs_the_named_steps_and_preserves_receipts
    def test_creation_runs_the_named_steps_and_preserves_receipts(self) -> None:
        """sapling.creation"""
        self.calls.run.side_effect = self.replies()
        with mock.patch('sapling_creation.merged_source',return_value='merged-source'):
            result = make_sapling(self.places,self.home/'readonly',commands=self.calls,
                                  inspector=lambda _places:self.inspector)
        self.assertTrue(result['current'])
        actual = [call.args[:2] for call in self.calls.run.call_args_list]
        self.assertEqual(actual,[('arbol-roots','list'),('arbol-roots','create'),('arbol-builds','build'),
                                 ('arbol-roots','migrate'),('arbol-roots','ready'),('arbol-roots','list'),
                                 ('arbol-root','--root')])
        self.assertEqual(len(list(Path(result['receipt']).glob('*.json'))),6)
        self.assertEqual(result['vendorRequests'],0)
# TEST-TIER-END tests/test_sapling_drills.py::Creation.test_creation_runs_the_named_steps_and_preserves_receipts

# TEST-TIER-BEGIN tests/test_sapling_drills.py::Creation.test_existing_or_unpublished_root_is_never_migrated_or_removed
    def test_existing_or_unpublished_root_is_never_migrated_or_removed(self) -> None:
        """sapling.creation-refusal"""
        for existing in ['catalogue','folder','settings']:
            self.calls.reset_mock()
            self.calls.run.side_effect = [[{'root':'sapling'}] if existing == 'catalogue' else []]
            target = self.places.roots/'sapling' if existing == 'folder' else self.home/'.arbol/roots/sapling'
            if existing != 'catalogue':
                target.mkdir(parents=True)
            with self.subTest(existing=existing),self.assertRaises(DrillError):
                make_sapling(self.places,self.home/'readonly',commands=self.calls)
            self.assertEqual(self.calls.run.call_count,1)
            if existing != 'catalogue':
                target.rmdir()
# TEST-TIER-END tests/test_sapling_drills.py::Creation.test_existing_or_unpublished_root_is_never_migrated_or_removed

# TEST-TIER-BEGIN tests/test_sapling_drills.py::Creation.test_failed_build_stops_before_migration_and_keeps_created_receipt
    def test_failed_build_stops_before_migration_and_keeps_created_receipt(self) -> None:
        """sapling.creation-failure"""
        replies = self.replies()
        replies[2] = {'root':'sapling','status':'failed'}
        self.calls.run.side_effect = replies
        with mock.patch('sapling_creation.merged_source',return_value='merged-source'):
            with self.assertRaises(DrillError):
                make_sapling(self.places,self.home/'readonly',commands=self.calls)
        self.assertEqual(self.calls.run.call_count,3)
        receipts = list((self.places.evidence/'creation-attempts').iterdir())
        self.assertEqual(len(receipts),1)
        self.assertTrue((receipts[0]/'created.json').is_file())
        self.assertEqual(json.loads((receipts[0]/'failure.json').read_text())['phase'],'build')
# TEST-TIER-END tests/test_sapling_drills.py::Creation.test_failed_build_stops_before_migration_and_keeps_created_receipt

# TEST-TIER-BEGIN tests/test_sapling_drills.py::Creation.test_branch_source_is_refused_before_create
    def test_branch_source_is_refused_before_create(self) -> None:
        """sapling.creation-source"""
        self.calls.run.return_value = []
        with mock.patch('sapling_creation.merged_source',side_effect=DrillError('unmerged source')):
            with self.assertRaises(DrillError):
                make_sapling(self.places,self.home/'branch',commands=self.calls)
        self.assertEqual(self.calls.run.call_count,1)
        self.assertFalse(self.places.evidence.exists())
# TEST-TIER-END tests/test_sapling_drills.py::Creation.test_branch_source_is_refused_before_create



class Messages(_support.Messages):
# TEST-TIER-BEGIN tests/test_sapling_drills.py::Messages.test_preflight_does_not_submit_and_two_explicit_submissions_keep_the_same_chat
    def test_preflight_does_not_submit_and_two_explicit_submissions_keep_the_same_chat(self) -> None:
        """sapling.messages"""
        preflight = real_messages(self.places,commands=self.calls)
        self.assertTrue(preflight['preflightOnly'])
        self.assertEqual(self.calls.starts,0)
        result = real_messages(self.places,send=True,commands=self.calls,inspector=self.inspector)
        self.assertEqual(result['submissions'],2)
        self.assertEqual(result['budget']['remaining'],8)
        self.assertEqual(result['reportedCostUSD'],'0.002')
        self.assertEqual([item['number'] for item in result['messages']],[1,2])
        self.assertNotIn('--chat',self.calls.requests[0]['arguments'])
        self.assertIn('--chat',self.calls.requests[1]['arguments'])
        self.assertTrue(result['messages'][1]['remembered'])
# TEST-TIER-END tests/test_sapling_drills.py::Messages.test_preflight_does_not_submit_and_two_explicit_submissions_keep_the_same_chat

# TEST-TIER-BEGIN tests/test_sapling_drills.py::Messages.test_ambiguous_start_counts_and_is_never_automatically_retried
    def test_ambiguous_start_counts_and_is_never_automatically_retried(self) -> None:
        """sapling.messages-ambiguous"""
        self.calls.fail_start = True
        with self.assertRaisesRegex(DrillError,'ambiguous acceptance'):
            real_messages(self.places,send=True,commands=self.calls,inspector=self.inspector)
        self.assertEqual(self.calls.starts,1)
        status = Budget(self.places.evidence).status()
        self.assertEqual(status['usedOrReserved'],1)
        self.assertEqual(status['attempts'][0]['state'],'ambiguous')
# TEST-TIER-END tests/test_sapling_drills.py::Messages.test_ambiguous_start_counts_and_is_never_automatically_retried

# TEST-TIER-BEGIN tests/test_sapling_drills.py::Messages.test_no_two_message_allowance_means_no_submission
    def test_no_two_message_allowance_means_no_submission(self) -> None:
        """sapling.messages-allowance"""
        for _ in range(9):
            Budget(self.places.evidence).reserve(str(uuid.uuid4()))
        with self.assertRaises(DrillError):
            real_messages(self.places,send=True,commands=self.calls,inspector=self.inspector)
        self.assertEqual(self.calls.starts,0)
# TEST-TIER-END tests/test_sapling_drills.py::Messages.test_no_two_message_allowance_means_no_submission

# TEST-TIER-BEGIN tests/test_sapling_drills.py::Messages.test_known_vendor_retry_deadline_blocks_even_a_cached_report_showing_available_capacity
    def test_known_vendor_retry_deadline_blocks_even_a_cached_report_showing_available_capacity(self) -> None:
        """sapling.messages-retry-deadline"""
        budget = Budget(self.places.evidence)
        exchange = str(uuid.uuid4())
        budget.reserve(exchange)
        budget.finish(exchange,'ambiguous',usage={'outcome':'failed','error':'rate_limited',
                                                 'retryNotBeforeUnix':time.time()+3600})
        with self.assertRaisesRegex(DrillError,'deadline has not passed'):
            real_messages(self.places,send=True,commands=self.calls,inspector=self.inspector)
        self.assertEqual(self.calls.starts,0)
# TEST-TIER-END tests/test_sapling_drills.py::Messages.test_known_vendor_retry_deadline_blocks_even_a_cached_report_showing_available_capacity

# TEST-TIER-BEGIN tests/test_sapling_drills.py::Messages.test_reached_or_unavailable_usage_never_submits
    def test_reached_or_unavailable_usage_never_submits(self) -> None:
        """sapling.messages-usage"""
        original = self.calls.run
        reports: list[dict[str,Any]] = [{'outcome':'unavailable','windows':[]},
                                       {'outcome':'ok','windows':[{'limitReached':True}]},
                                       {'outcome':'ok','windows':[{'usedPercent':100}]}]
        for report in reports:
            def run(program: str, *args: str, selected: dict[str, Any] = report, **options: Any) -> Any:
                if program == 'arbol-claude-driver' and 'usage' in args:
                    return selected
                return original(program,*args,**options)
            with mock.patch.object(self.calls,'run',side_effect=run):
                with self.assertRaises(DrillError):
                    real_messages(self.places,send=True,commands=self.calls,inspector=self.inspector)
        self.assertEqual(self.calls.starts,0)
# TEST-TIER-END tests/test_sapling_drills.py::Messages.test_reached_or_unavailable_usage_never_submits

# TEST-TIER-BEGIN tests/test_sapling_drills.py::Messages.test_elapsed_cached_limit_permits_one_explicit_same_chat_pair
    def test_elapsed_cached_limit_permits_one_explicit_same_chat_pair(self) -> None:
        """sapling.messages-expired-usage"""
        original = self.calls.run
        report: dict[str,Any] = {'outcome':'ok','fetchedAt':'2000-01-01T00:00:00Z',
                  'windows':[{'limitReached':True,'usedPercent':104,'resetsAt':'2000-01-01T01:00:00Z'},
                             {'kind':'weekly','usedPercent':20,'limitReached':False}]}

        def run(program: str, *args: str, **options: Any) -> Any:
            if program == 'arbol-claude-driver' and 'usage' in args:
                return report
            return original(program,*args,**options)

        with mock.patch.object(self.calls,'run',side_effect=run):
            result = real_messages(self.places,send=True,commands=self.calls,inspector=self.inspector)
        self.assertTrue(result['passed'])
        self.assertEqual(self.calls.starts,2)
        self.assertEqual(report['windows'][0]['usedPercent'],104)
# TEST-TIER-END tests/test_sapling_drills.py::Messages.test_elapsed_cached_limit_permits_one_explicit_same_chat_pair

# TEST-TIER-BEGIN tests/test_sapling_drills.py::Messages.test_elapsed_window_does_not_hide_unknown_future_or_other_active_limits
    def test_elapsed_window_does_not_hide_unknown_future_or_other_active_limits(self) -> None:
        """sapling.messages-unproved-reset"""
        original = self.calls.run
        expired = {'limitReached':True,'resetsAt':'2000-01-01T01:00:00Z'}
        reports: list[dict[str,Any]] = [
            {'outcome':'ok','windows':[expired]},
            {'outcome':'ok','fetchedAt':'invalid','windows':[expired]},
            {'outcome':'ok','fetchedAt':'2000-01-01T00:00:00','windows':[expired]},
            {'outcome':'ok','fetchedAt':'2000-01-01T02:00:00Z','windows':[expired]},
            {'outcome':'ok','fetchedAt':'2000-01-01T00:00:00Z',
             'windows':[{'limitReached':True,'resetsAt':'2099-01-01T00:00:00Z'}]},
            {'outcome':'ok','fetchedAt':'2000-01-01T00:00:00Z',
             'windows':[{'limitReached':True,'resetsAt':'invalid'}]},
            {'outcome':'ok','fetchedAt':'2000-01-01T00:00:00Z',
             'windows':[expired,{'usedPercent':100,'resetsAt':'2099-01-01T00:00:00Z'}]},
        ]
        for report in reports:
            def run(program: str, *args: str, selected: dict[str,Any] = report, **options: Any) -> Any:
                if program == 'arbol-claude-driver' and 'usage' in args:
                    return selected
                return original(program,*args,**options)
            with self.subTest(report=report),mock.patch.object(self.calls,'run',side_effect=run):
                with self.assertRaises(DrillError):
                    real_messages(self.places,send=True,commands=self.calls,inspector=self.inspector)
        self.assertEqual(self.calls.starts,0)
# TEST-TIER-END tests/test_sapling_drills.py::Messages.test_elapsed_window_does_not_hide_unknown_future_or_other_active_limits

# TEST-TIER-BEGIN tests/test_sapling_drills.py::Messages.test_judgement_refuses_lost_history_wrong_route_or_missing_usage
    def test_judgement_refuses_lost_history_wrong_route_or_missing_usage(self) -> None:
        """sapling.messages-judgement"""
        request = self.places.evidence/'request.json'
        new_json(request,{'message':'Remember this word for this chat: pinefixture. Reply remembered.',
                          'route':{'driver':'claude','subscription':'anthropic','model':'haiku'}})
        accepted = self.calls.run('arbol-root','start','--exchange',str(uuid.uuid4()),'--request',str(request))
        good = self.calls.data()
        for case in ['word','route','tokens']:
            data = json.loads(json.dumps(good))
            if case == 'route':
                data['exchange']['route']['model'] = 'other'
            elif case == 'tokens':
                data['runs'][0]['usage'] = {}
            with self.subTest(case=case),self.assertRaises(DrillError):
                judge(data,accepted,self.calls.requests[0]['request']['message'],1,
                      remembered='not-the-remembered-word' if case == 'word' else None)
# TEST-TIER-END tests/test_sapling_drills.py::Messages.test_judgement_refuses_lost_history_wrong_route_or_missing_usage
