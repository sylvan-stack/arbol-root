"""The Root manager's short-lived command line (RTM-0)."""

from __future__ import annotations

import json
import sys
from pathlib import Path

from arbol_root.input import Command
from arbol_root.input import parse as parse_command
from arbol_root.launcher import list_reply
from arbol_root.listing import listing
from arbol_root.model import Refusal, identity
from arbol_root.start import start


def parse(args: list[str]) -> Command:
    return parse_command(args)


def trunks(root: str, code: list[str], bin_dir: Path) -> int:
    reply = list_reply(root, code, bin_dir)
    sys.stdout.buffer.write(reply.raw)
    return reply.status


def main(args: list[str] | None = None, *, package: Path | None = None) -> int:
    try:
        command = parse(sys.argv[1:] if args is None else args)
        context = identity(package or Path(__file__).resolve().parents[2], command.options)
        if command.name == 'trunks':
            return trunks(context.root, [] if command.code is None else [command.code], context.bin_dir)
        if command.name == 'start':
            reply = start(context, command)
            sys.stdout.buffer.write(reply.raw)
            return reply.status
        print(json.dumps(listing(context), ensure_ascii=True))
        return 0
    except Refusal as error:
        document: dict[str, object] = {'error':{'code':error.code, 'message':str(error)}}
        if error.available is not None:
            document['available'] = error.available
        print(json.dumps(document, ensure_ascii=False))
        return 1
