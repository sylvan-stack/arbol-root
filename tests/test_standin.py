from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class StandIn(unittest.TestCase):
    def test_scripts_list_run_fragments_and_process_observation(self) -> None:
        """root.standin"""
        with tempfile.TemporaryDirectory(prefix='rtm-standin-') as temp:
            base = Path(temp).resolve()
            program = base / 'standin.py'
            program.write_bytes((ROOT / 'tests/standin_trunk.py').read_bytes())
            script = {'responses':{'list':{'stdout':'{"trunks":[]}\n'}, 'run':{
                'fragments':[{'text':'{"accepted":','delay':0.02}, {'text':'true}\n'}],
                'stderr':'diagnostic\n','status':1}}}
            (base / 'script.json').write_text(json.dumps(script))
            env = {'HOME':str(base), 'PATH':'/usr/bin:/bin', 'LANG':'en_US.UTF-8'}
            for command, line, status in [('list', b'{"trunks":[]}\n', 0), ('run', b'{"accepted":true}\n', 1)]:
                with self.subTest(command=command):
                    process = subprocess.Popen([sys.executable,'-I','-B',str(program),'--root','sapling',command],
                                               env=env, cwd=base, start_new_session=True,
                                               stdin=subprocess.DEVNULL, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                    output, errors = process.communicate(timeout=5)
                    self.assertEqual((output, process.returncode), (line, status))
                    if command == 'run':
                        self.assertEqual(errors, b'diagnostic\n')
                    call = json.loads((base / 'calls.jsonl').read_text().splitlines()[-1])
                    self.assertEqual(call['args'], ['--root','sapling',command])
                    self.assertEqual((call['pid'],call['pgid'],call['sid']), (process.pid,)*3)
                    self.assertEqual(call['cwd'], str(base))
                    self.assertTrue(call['stdinNull'])
                    self.assertEqual((call['home'],call['path']), (str(base),'/usr/bin:/bin'))

    def test_detached_reply_closes_pipes_before_the_stand_in_ends(self) -> None:
        with tempfile.TemporaryDirectory(prefix='rtm-standin-') as temp:
            base = Path(temp).resolve()
            program = base / 'standin.py'
            program.write_bytes((ROOT / 'tests/standin_trunk.py').read_bytes())
            (base / 'script.json').write_text('{"stdout":"{}\\n", "detach":true, "hold":true}')
            process = subprocess.Popen([sys.executable,'-I','-B',str(program),'run'],
                                       env={**os.environ,'HOME':str(base)}, cwd=base, start_new_session=True,
                                       stdin=subprocess.DEVNULL, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            try:
                assert process.stdout is not None and process.stderr is not None
                self.assertEqual(process.stdout.read(), b'{}\n')
                self.assertIsNone(process.poll())
            finally:
                (base / 'release').touch()
                process.wait(timeout=5)
                assert process.stdout is not None and process.stderr is not None
                process.stdout.close()
                process.stderr.close()
