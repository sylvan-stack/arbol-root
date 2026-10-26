"""A scripted launcher used only in tests (RTM-0.15, start/list)."""

import json
import os
import shutil
import stat
import sys
import time
from pathlib import Path

base = Path(__file__).resolve().parent
script = json.loads((base / 'script.json').read_text())
command = next((name for name in ['run', 'settle'] if name in sys.argv[1:]), 'list')
script = {**script, **script.get('responses', {}).get(command, {})}
if command == 'settle':
    script = {**script, **script.get('outcomes', {}).get(sys.argv[-1], {})}
    if 'settled' in script:
        script['stdout'] = json.dumps({'exchange':sys.argv[-1], 'settled':script['settled']})+'\n'
    if script.get('removeExchange'):
        shutil.rmtree(Path(script['removeExchange']) / sys.argv[-1])
stdin = os.fstat(0)
null = os.stat('/dev/null')
call = {'args':sys.argv[1:], 'path':os.environ['PATH'], 'home':os.environ['HOME'],
        'pid':os.getpid(), 'pgid':os.getpgrp(), 'sid':os.getsid(0), 'cwd':os.getcwd(),
        'stdinNull':stat.S_ISCHR(stdin.st_mode) and stdin.st_rdev == null.st_rdev}
fd = os.open(base / 'calls.jsonl', os.O_WRONLY | os.O_CREAT | os.O_APPEND, 0o600)
try:
    os.write(fd, (json.dumps(call)+'\n').encode())
finally:
    os.close(fd)
while script.get('holdReply') and not (base / 'reply-release').exists():
    time.sleep(0.01)
time.sleep(script.get('delay', 0))
sys.stderr.buffer.write(script.get('stderr', '').encode())
sys.stderr.buffer.flush()
if 'fragments' in script:
    for fragment in script['fragments']:
        sys.stdout.buffer.write(fragment['text'].encode())
        sys.stdout.buffer.flush()
        time.sleep(fragment.get('delay', 0))
else:
    sys.stdout.buffer.write(script.get('stdout', '{}').encode())
    sys.stdout.buffer.flush()
if script.get('detach'):
    fd = os.open('/dev/null', os.O_RDWR)
    try:
        os.dup2(fd, 1)
        os.dup2(fd, 2)
    finally:
        os.close(fd)
while script.get('hold') and not (base / 'release').exists():
    time.sleep(0.01)
time.sleep(script.get('linger', 0))
raise SystemExit(script.get('status', 0))
