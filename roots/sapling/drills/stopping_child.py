"""One explicitly disposable same-group child for the five-second force drill."""

import json
import os
import signal
import sys
from pathlib import Path


def main() -> None:
    folder = Path(sys.argv[1])/'standin'

    def ignore(number: int, frame: object) -> None:
        fd = os.open(folder/'ignored-signals.jsonl',os.O_WRONLY | os.O_APPEND | os.O_CREAT | os.O_NOFOLLOW,0o600)
        try:
            os.write(fd,(json.dumps({'pid':os.getpid(),'signal':number})+'\n').encode())
        finally:
            os.close(fd)

    signal.signal(signal.SIGTERM,ignore)
    temporary = folder/'ignored-child.new'
    with temporary.open('x') as stream:
        json.dump({'pid':os.getpid(),'group':os.getpgrp()},stream)
    temporary.replace(folder/'ignored-child.json')
    while True:
        signal.pause()


if __name__ == '__main__':
    main()
