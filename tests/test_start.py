from __future__ import annotations

import json
import os
import shlex
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from typing import Any, cast
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))
from arbol_root.input import parse  # noqa: E402
from arbol_root.model import Identity, Refusal  # noqa: E402
from arbol_root.start import start  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
EXCHANGE = '7f3a2c1e-4b5d-4e6f-8a9b-0c1d2e3f4a5b'
ACCEPTED = '  { "accepted":true, "root":"sapling", "exchange":"'+EXCHANGE+'", "extra":3 }\n'
INVENTORY = {'root':'sapling','rootContract':1,'trunks':[{'trunk':'trivial','builds':[
    {'build':'a','status':'working','fits':True,'runnable':True,'chosen':True}]}]}
POPEN = subprocess.Popen


class Starting(unittest.TestCase):
    def setUp(self) -> None:
        temp = tempfile.TemporaryDirectory(prefix='rtm-start-')
        self.addCleanup(temp.cleanup)
        self.base = Path(temp.name).resolve()
        self.bin = self.base / 'launchers with spaces'
        self.bin.mkdir()
        shutil.copy2(ROOT / 'tests/standin_trunk.py', self.bin / 'standin.py')
        program = self.bin / 'arbol-trunk'
        program.write_text('#!/bin/sh\nexec '+shlex.quote(sys.executable)+' -I -B '+
                           shlex.quote(str(self.bin / 'standin.py'))+' "$@"\n')
        program.chmod(0o755)
        self.root = self.base / 'root'
        self.root.mkdir()
        (self.root / 'root.json').write_text('{"root":"sapling"}')
        self.request = self.base / 'request with spaces'
        self.request.write_bytes(b'\xff the manager never opens this file')
        self.options = ['--exchange',EXCHANGE,'--request',str(self.request)]
        self.context = Identity('sapling','0','1.0.0',self.root,self.bin)
        self.children: list[subprocess.Popen[bytes]] = []
        self.addCleanup(self.clean_children)
        self.script()

    def clean_children(self) -> None:
        for child in self.children:
            if child.poll() is None:
                child.terminate()
            child.wait(timeout=5)

    def spawn(self, *args: Any, **kwargs: Any) -> subprocess.Popen[bytes]:
        child = cast(subprocess.Popen[bytes], POPEN(*args, **kwargs))
        self.children.append(child)
        return child

    def script(self, **run: object) -> None:
        (self.bin / 'script.json').write_text(json.dumps({'responses':{
            'list':{'stdout':json.dumps(INVENTORY)+'\n'}, 'run':{'stdout':ACCEPTED, **run}}}))

    def calls(self) -> list[dict[str, Any]]:
        return [json.loads(line) for line in (self.bin / 'calls.jsonl').read_text().splitlines()]

    def cli(self, extra: list[str] | None = None) -> subprocess.CompletedProcess[bytes]:
        return subprocess.run([sys.executable,'-I','-B',str(ROOT / 'bin/entry.py'),'--root','sapling',
                               '--root-dir',str(self.root),'--bin-dir',str(self.bin),'start',*self.options,*(extra or [])],
                              env={**os.environ,'HOME':str(self.base)}, cwd=self.base,
                              capture_output=True, check=False, timeout=10)

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

    def test_explicit_build_skips_list_and_does_not_read_a_fifo_request(self) -> None:
        """root.start-no-request-read"""
        self.request.unlink()
        os.mkfifo(self.request)
        result = self.cli(['advanced','-v','b'])
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(len(self.calls()), 1)
        self.assertEqual(self.calls()[0]['args'][:6], ['--root','sapling','advanced','-v','b','run'])
        self.assertFalse(self.request.exists())

    def test_refusal_line_is_unchanged_and_also_removes_request(self) -> None:
        """root.start-refusal"""
        line = ' {"error":{"code":"chat_busy","message":"busy","detail":4},"available":["a"]}\n'
        self.script(stdout=line,status=1,stderr='Trunk diagnostic\n')
        result = self.cli(['-v','a'])
        self.assertEqual((result.returncode,result.stdout,result.stderr), (1,line.encode(),b'Trunk diagnostic\n'))
        self.assertFalse(self.request.exists())

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
