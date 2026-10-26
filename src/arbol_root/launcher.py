"""Query the external Trunk launcher; no Build registry is read here."""

from __future__ import annotations

import json
import os
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from arbol_root.input import Command
from arbol_root.model import BUILD_ID, Identity, Refusal


@dataclass(frozen=True)
class Reply:
    raw: bytes
    value: dict[str, Any]
    status: int


def launcher_environment(bin_dir: Path) -> dict[str, str]:
    return {**os.environ, 'PATH':str(bin_dir.absolute())+os.pathsep+os.environ.get('PATH', os.defpath)}


def object_line(line: bytes) -> dict[str, Any] | None:
    try:
        value = json.loads(line.decode('utf-8'))
    except (UnicodeError, ValueError):
        return None
    return value if isinstance(value, dict) else None


def list_reply(root: str, code: list[str], bin_dir: Path) -> Reply:
    executable = bin_dir.absolute() / 'arbol-trunk'
    try:
        result = subprocess.run([str(executable),'--root',root,*code,'list'], env=launcher_environment(bin_dir),
                                stdin=subprocess.DEVNULL, capture_output=True, check=False)
    except (OSError, ValueError) as error:
        raise Refusal('trunk_unavailable', f'Cannot start {executable}: {error}') from error
    sys.stderr.buffer.write(result.stderr)
    for line in result.stdout.splitlines(keepends=True):
        value = object_line(line)
        if value is not None:
            return Reply(line, value, 1 if 'error' in value or result.returncode != 0 else 0)
    raise Refusal('trunk_unavailable', f'{executable} list ended without a JSON-object line.')


def select_build(context: Identity, command: Command) -> str | Reply:
    if '-v' in command.options:
        return command.options['-v']
    reply = list_reply(context.root, [command.code], context.bin_dir)
    if 'error' in reply.value:
        return reply
    try:
        value = reply.value
        if (reply.status or value['root'] != context.root or type(value['rootContract']) is not int
                or value['rootContract'] < 1 or not isinstance(value['trunks'], list)):
            raise ValueError
        entries = [item for item in value['trunks'] if isinstance(item, dict) and item.get('trunk') == command.code]
        if len(entries) != 1 or not isinstance(entries[0].get('builds'), list):
            raise ValueError
        records = entries[0]['builds']
        numbers: set[str] = set()
        for item in records:
            if (not isinstance(item, dict) or not isinstance(item.get('build'), str)
                    or not BUILD_ID.fullmatch(item['build']) or item['build'] in numbers
                    or not isinstance(item.get('status'), str)
                    or any(type(item.get(key)) is not bool for key in ['fits','runnable','chosen'])):
                raise ValueError
            numbers.add(item['build'])
        chosen = [item for item in records if item['chosen']]
        if len(chosen) > 1 or any(not item['fits'] or not item['runnable'] or item['status'] != 'working' for item in chosen):
            raise ValueError
    except (KeyError, TypeError, ValueError):
        raise Refusal('trunk_unavailable', 'arbol-trunk list returned an unreadable inventory for this Root/Trunk.') from None
    if not chosen:
        available = [item['build'] for item in records if item['fits'] and item['runnable']]
        raise Refusal('no_fit', f'No chosen Build of {command.code} fits Root {context.root}.', available)
    return str(chosen[0]['build'])
