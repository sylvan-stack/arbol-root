"""Mid-tier selections. Write or run only in an explicitly requested testing task."""
from __future__ import annotations

import test_start as _support
from test_start import (
    ACCEPTED,
    Any,
    EXCHANGE,
    INVENTORY,
    Identity,
    POPEN,
    Path,
    ROOT,
    Refusal,
    Starting,
    cast,
    development,
    json,
    mock,
    os,
    parse,
    shlex,
    shutil,
    start,
    subprocess,
    sys,
    tempfile,
    unittest,
)


class Starting(_support.Starting):
# TEST-TIER-BEGIN tests/test_start.py::Starting.test_cli_chooses_exact_build_preserves_options_group_stdin_and_cwd
    def test_cli_chooses_exact_build_preserves_options_group_stdin_and_cwd(self) -> None:
        """root.start-launch"""
        extra = ['--model=two words','--cwd',str(self.base),'--subscription','test',
                 '--driver=claude','--effort=high','--chat',EXCHANGE,'--replaces',EXCHANGE]
        result = self.cli(extra)
        self.assertEqual((result.returncode,result.stdout), (0,ACCEPTED.encode()), result.stderr)
        calls = self.calls()
        self.assertEqual(calls[0]['args'], ['--root','sapling','trivial','list'])
        run = calls[1]
        self.assertEqual(run['args'], ['--root','sapling','trivial','-v','a','run','--detach',*self.options,*extra])
        self.assertEqual((run['pid'],run['pgid'],run['sid']), (run['pid'],)*3)
        self.assertTrue(run['stdinNull'])
        self.assertEqual(run['cwd'], str(self.base))
        self.assertEqual(run['path'].split(os.pathsep)[0], str(self.bin))
        self.assertFalse(self.request.exists())
# TEST-TIER-END tests/test_start.py::Starting.test_cli_chooses_exact_build_preserves_options_group_stdin_and_cwd

# TEST-TIER-BEGIN tests/test_start.py::Starting.test_explicit_build_skips_list_and_does_not_read_a_fifo_request
    def test_explicit_build_skips_list_and_does_not_read_a_fifo_request(self) -> None:
        """root.start-no-request-read"""
        self.request.unlink()
        os.mkfifo(self.request)
        result = self.cli(['advanced','-v','b'])
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(len(self.calls()), 1)
        self.assertEqual(self.calls()[0]['args'][:6], ['--root','sapling','advanced','-v','b','run'])
        self.assertFalse(self.request.exists())
# TEST-TIER-END tests/test_start.py::Starting.test_explicit_build_skips_list_and_does_not_read_a_fifo_request

# TEST-TIER-BEGIN tests/test_start.py::Starting.test_refusal_line_is_unchanged_and_also_removes_request
    def test_refusal_line_is_unchanged_and_also_removes_request(self) -> None:
        """root.start-refusal"""
        line = ' {"error":{"code":"chat_busy","message":"busy","detail":4},"available":["a"]}\n'
        self.script(stdout=line,status=1,stderr='Trunk diagnostic\n')
        result = self.cli(['-v','a'])
        self.assertEqual((result.returncode,result.stdout,result.stderr), (1,line.encode(),b'Trunk diagnostic\n'))
        self.assertFalse(self.request.exists())
# TEST-TIER-END tests/test_start.py::Starting.test_refusal_line_is_unchanged_and_also_removes_request

# TEST-TIER-BEGIN tests/test_start.py::Starting.test_eof_without_object_preserves_request_and_final_unterminated_object_is_accepted
    def test_eof_without_object_preserves_request_and_final_unterminated_object_is_accepted(self) -> None:
        """root.start-eof"""
        self.script(stdout='not JSON\n[]\n')
        result = self.cli(['-v','a'])
        self.assertEqual(json.loads(result.stdout)['error']['code'], 'no_answer')
        self.assertTrue(self.request.exists())
        self.script(stdout=' {"accepted":true}',status=2)
        result = self.cli(['-v','a'])
        self.assertEqual((result.returncode,result.stdout), (0,b' {"accepted":true}'))
        self.assertFalse(self.request.exists())
# TEST-TIER-END tests/test_start.py::Starting.test_eof_without_object_preserves_request_and_final_unterminated_object_is_accepted

# TEST-TIER-BEGIN tests/test_start.py::Starting.test_preflight_refusal_or_no_fit_does_not_start_run_or_remove_request
    def test_preflight_refusal_or_no_fit_does_not_start_run_or_remove_request(self) -> None:
        line = ' {"error":{"code":"unknown_trunk"},"available":[]}\n'
        (self.bin / 'script.json').write_text(json.dumps({'stdout':line,'status':1}))
        result = self.cli()
        self.assertEqual((result.returncode,result.stdout), (1,line.encode()))
        self.assertEqual(len(self.calls()), 1)
        self.assertTrue(self.request.exists())
        inventory = json.loads(json.dumps(INVENTORY))
        inventory['trunks'][0]['builds'][0]['chosen'] = False
        (self.bin / 'script.json').write_text(json.dumps({'stdout':json.dumps(inventory)}))
        result = self.cli()
        value = json.loads(result.stdout)
        self.assertEqual((result.returncode,value['error']['code'],value['available']), (1,'no_fit',['a']))
        self.assertEqual(len(self.calls()), 2)
        self.assertTrue(self.request.exists())
# TEST-TIER-END tests/test_start.py::Starting.test_preflight_refusal_or_no_fit_does_not_start_run_or_remove_request

# TEST-TIER-BEGIN tests/test_start.py::Starting.test_cleanup_failure_is_diagnostic_after_a_reply_and_spawn_failure_keeps_request
    def test_cleanup_failure_is_diagnostic_after_a_reply_and_spawn_failure_keeps_request(self) -> None:
        """root.start-cleanup"""
        with (mock.patch('arbol_root.start.Path.unlink',side_effect=PermissionError('private fixture')),
              mock.patch('arbol_root.start.subprocess.Popen',side_effect=self.spawn)):
            reply = start(self.context,parse(['start',*self.options,'-v','a']))
        self.assertEqual((reply.status,reply.raw), (0,ACCEPTED.encode()))
        self.assertTrue(self.request.exists())
        (self.bin / 'arbol-trunk').unlink()
        result = self.cli(['-v','a'])
        self.assertEqual(json.loads(result.stdout)['error']['code'], 'trunk_unavailable')
        self.assertTrue(self.request.exists())
# TEST-TIER-END tests/test_start.py::Starting.test_cleanup_failure_is_diagnostic_after_a_reply_and_spawn_failure_keeps_request
