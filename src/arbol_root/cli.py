"""The Root manager's short-lived command line (RTM-0)."""

from __future__ import annotations

import json
import sys
from pathlib import Path

from arbol_root.launcher import list_reply
from arbol_root.model import Refusal, identity

OPTIONS = {"--root", "--root-dir", "--bin-dir"}


def parse(args: list[str]) -> tuple[str, list[str], dict[str, str]]:
    words: list[str] = []
    options: dict[str, str] = {}
    i = 0
    while i < len(args):
        word = args[i]
        if word.startswith("-"):
            key, equal, value = word.partition("=")
            if key not in OPTIONS or key in options:
                raise Refusal("invalid_input", f"Unknown or repeated option: {key}")
            if not equal:
                i += 1
                if i >= len(args) or args[i].startswith("-"):
                    raise Refusal("invalid_input", f"{key} needs a value.")
                value = args[i]
            if not value:
                raise Refusal("invalid_input", f"{key} needs a value.")
            options[key] = value
        else:
            words.append(word)
        i += 1
    if not words or words[0] != "trunks" or len(words) > 2:
        raise Refusal("invalid_input", "Expected trunks [<code name>].")
    return words[0], words[1:], options


def trunks(root: str, code: list[str], bin_dir: Path) -> int:
    reply = list_reply(root, code, bin_dir)
    sys.stdout.buffer.write(reply.raw)
    return reply.status


def main(args: list[str] | None = None, *, package: Path | None = None) -> int:
    try:
        _command, code, options = parse(sys.argv[1:] if args is None else args)
        context = identity(package or Path(__file__).resolve().parents[2], options)
        return trunks(context.root, code, context.bin_dir)
    except Refusal as error:
        print(json.dumps({"error": {"code": error.code, "message": str(error)}}, ensure_ascii=False))
        return 1
