"""Start one exact Trunk Build and leave it independent of this short-lived manager."""

from __future__ import annotations

import os
import subprocess
import sys
import tempfile
import time
from pathlib import Path
from typing import BinaryIO

from arbol_root.input import Command
from arbol_root.launcher import Reply, launcher_environment, object_line, select_build
from arbol_root.model import Identity, Refusal

ACCEPT_SECONDS = 20.0


def wait_reply(child: subprocess.Popen[bytes], output: BinaryIO, timeout: float) -> Reply | None:
    deadline = time.monotonic()+timeout
    pending = b''
    offset = 0
    while True:
        data = os.pread(output.fileno(), 65536, offset)
        offset += len(data)
        pending += data
        while b'\n' in pending:
            line, _separator, pending = pending.partition(b'\n')
            line += b'\n'
            value = object_line(line)
            if value is not None:
                return Reply(line, value, 1 if 'error' in value else 0)
        ended = child.poll() is not None
        if ended and not data:
            value = object_line(pending)
            return Reply(pending, value, 1 if 'error' in value else 0) if value is not None else None
        remaining = deadline-time.monotonic()
        if remaining <= 0:
            return None
        if not data:
            time.sleep(min(0.01, remaining))


def start(context: Identity, command: Command, *, timeout: float = ACCEPT_SECONDS) -> Reply:
    selected = select_build(context, command)
    if isinstance(selected, Reply):
        return selected  # A preflight refusal never touches the request.
    assert command.code is not None
    request = command.options['--request']
    executable = context.bin_dir.absolute() / 'arbol-trunk'
    args = [str(executable),'--root',context.root,command.code,'-v',selected,'run','--detach',
            '--exchange',command.options['--exchange'],'--request',request,*command.forward]
    # Anonymous files keep late output independent of the manager, including after no_answer.
    with tempfile.TemporaryFile() as output, tempfile.TemporaryFile() as diagnostics:
        try:
            child = subprocess.Popen(args, env=launcher_environment(context.bin_dir), start_new_session=True,
                                     stdin=subprocess.DEVNULL, stdout=output, stderr=diagnostics)
        except (OSError, ValueError) as error:
            raise Refusal('trunk_unavailable', f'Cannot start {executable}: {error}') from error
        try:
            reply = wait_reply(child, output, timeout)
        finally:
            size = os.fstat(diagnostics.fileno()).st_size
            sys.stderr.buffer.write(os.pread(diagnostics.fileno(), size, 0))
        if reply is None:
            raise Refusal('no_answer', 'The Trunk gave no JSON-object line within 20 seconds or before it ended.')
    try:
        Path(request).unlink(missing_ok=True)
    except OSError as error:
        print(f'The Trunk replied, but the request name could not be removed: {error}', file=sys.stderr)
    return reply
