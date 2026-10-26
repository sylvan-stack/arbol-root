"""Command input, without opening the request or running a Trunk."""

from __future__ import annotations

import re
from dataclasses import dataclass

from arbol_root.model import BUILD_ID, Refusal

COMMON = {'--root', '--root-dir', '--bin-dir'}
FORWARD = {'--chat', '--replaces', '--cwd', '--driver', '--subscription', '--model', '--effort'}
START = {'--exchange', '--request', '-v'} | FORWARD
UUID = re.compile(r'[0-9a-fA-F]{8}(?:-[0-9a-fA-F]{4}){3}-[0-9a-fA-F]{12}\Z', re.ASCII)


@dataclass(frozen=True)
class Command:
    name: str
    code: str | None
    options: dict[str, str]
    forward: list[str]


def parse(args: list[str]) -> Command:
    words: list[str] = []
    options: dict[str, str] = {}
    forward: list[str] = []
    index = 0
    while index < len(args):
        word = args[index]
        if word.startswith('-'):
            key, equals, value = word.partition('=')
            if key not in COMMON and not (words and words[0] == 'start' and key in START):
                raise Refusal('invalid_input', f'Unknown or misplaced option: {key}')
            if key in options:
                raise Refusal('invalid_input', f'Repeated option: {key}')
            tokens = [word]
            if not equals:
                index += 1
                if index >= len(args) or args[index].startswith('-'):
                    raise Refusal('invalid_input', f'{key} needs a value.')
                value = args[index]
                tokens.append(value)
            if not value:
                raise Refusal('invalid_input', f'{key} needs a value.')
            options[key] = value
            if key in FORWARD:
                forward.extend(tokens)
        else:
            words.append(word)
        index += 1
    if not words or words[0] not in {'trunks', 'start', 'list'}:
        raise Refusal('invalid_input', 'Expected trunks, start or list.')
    name = words[0]
    if len(words) > (1 if name == 'list' else 2):
        raise Refusal('invalid_input', f'Surplus argument for {name}.')
    if name == 'start':
        if not UUID.fullmatch(options.get('--exchange', '')) or '--request' not in options:
            raise Refusal('invalid_input', 'start requires --exchange <UUID> and --request <file>.')
        if '-v' in options and not BUILD_ID.fullmatch(options['-v']):
            raise Refusal('invalid_input', '-v needs a positive lower-case hexadecimal Build number.')
    return Command(name, words[1] if len(words) == 2 else ('trivial' if name == 'start' else None), options, forward)
