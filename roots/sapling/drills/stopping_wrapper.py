"""A private Driver wrapper starts a deliberately stubborn child only for an explicit run."""

import json
import os
import subprocess
import sys
from pathlib import Path


def main() -> None:
    home,base,child = sys.argv[1:4]
    args = sys.argv[4:]
    if args[:1] == ['run']:
        process = subprocess.Popen([sys.executable,'-IB',child,home],stdin=subprocess.DEVNULL,
                                   stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
        fd = os.open(Path(home)/'standin/children.jsonl',os.O_WRONLY | os.O_APPEND | os.O_CREAT | os.O_NOFOLLOW,0o600)
        try:
            os.write(fd,(json.dumps({'pid':process.pid,'runId':'ignored-term-child'})+'\n').encode())
        finally:
            os.close(fd)
    os.execv(base,[base,*args])


if __name__ == '__main__':
    main()
