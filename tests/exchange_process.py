"""A private process-group leader for stop tests; never launched outside a test folder."""

import json
import signal
import subprocess
import sys
import time
from pathlib import Path

folder = Path(sys.argv[1])
mode = sys.argv[2]
if mode == 'ignore':
    signal.signal(signal.SIGTERM, signal.SIG_IGN)
if mode in {'child', 'ignore'}:
    child = subprocess.Popen([sys.executable, '-I', '-B', '-c',
                              'import signal,time,sys; from pathlib import Path; '
                              'signal.signal(signal.SIGTERM,signal.SIG_IGN); Path(sys.argv[1]).touch(); time.sleep(120)',
                              str(folder / 'child-ready')])
    (folder / 'child-pid').write_text(str(child.pid))
    while not (folder / 'child-ready').exists():
        time.sleep(0.01)
(folder / 'ready').touch()
while not (folder / 'release').exists():
    if mode in {'cooperate', 'remove'} and any(json.loads(line).get('type') == 'stop'
                                             for line in (folder / 'control').read_text().splitlines()):
        if mode == 'remove':
            import shutil
            shutil.rmtree(folder)
        else:
            record = json.loads((folder / 'record.json').read_text())
            record['end'] = {'state':'cancelled', 'at':'2026-10-26T12:00:00.000Z'}
            temporary = folder / 'record.tmp'
            temporary.write_text(json.dumps(record))
            temporary.replace(folder / 'record.json')
        break
    time.sleep(0.01)
