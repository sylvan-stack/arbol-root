"""Root-owned optional migration capabilities and deterministic psql branch selection (RTM-D28)."""

from __future__ import annotations

import json
import re
import stat
from pathlib import Path
from typing import Any

FILE = 'migration-modes.json'
CAPABILITY = {'version':1,'modes':['check','chat']}
PRESENCE = re.compile(r':\{\?(arbol_migrate_(?:chat|check))\}')


def read_modes(path: Path, *, optional: bool = False) -> dict[str, Any] | None:
    try:
        info = path.lstat()
    except FileNotFoundError:
        if optional:
            return None
        raise ValueError('The advertised migration capability file is missing.') from None
    if not stat.S_ISREG(info.st_mode):
        raise ValueError('The migration capability must be a regular file, not a link.')
    value = json.loads(path.read_bytes())
    if (not isinstance(value,dict) or set(value) != {'version','modes'} or type(value.get('version')) is not int
            or value != CAPABILITY):
        raise ValueError('The migration capability must be version 1 with exactly check and chat modes.')
    return dict(value)


def branch(source: str, mode: str = 'whole') -> str:
    """Select only fixed documented presence tests; no shell expansion or arbitrary expression is accepted."""
    selected = {'whole':set(), 'check':{'arbol_migrate_check'}, 'chat':{'arbol_migrate_chat'},
                'both':{'arbol_migrate_chat','arbol_migrate_check'}}
    if mode not in selected:
        raise ValueError('Unknown migration protocol mode.')
    # Each level holds the parent's inclusion, whether a prior arm won, whether else was seen, and this arm.
    stack: list[tuple[bool,bool,bool,bool]] = []
    enabled = True
    out = []
    saw = False
    for line in source.splitlines():
        command = line.strip().split(maxsplit=1)
        token = command[0] if command else ''
        if token in ('\\if','\\elif'):
            saw = True
            match = PRESENCE.fullmatch(command[1]) if len(command) == 2 else None
            if match is None:
                raise ValueError('Migration conditionals use only the two documented presence flags.')
            present = match[1] in selected[mode]
            if token == '\\if':
                stack.append((enabled,present,False,enabled and present))
            else:
                if not stack or stack[-1][2]:
                    raise ValueError('Unexpected migration elif.')
                parent,won,otherwise,_arm = stack.pop()
                stack.append((parent,won or present,otherwise,parent and not won and present))
            enabled = stack[-1][3]
        elif token == '\\else':
            if len(command) != 1 or not stack or stack[-1][2]:
                raise ValueError('Unexpected migration else.')
            parent,won,_otherwise,_arm = stack.pop()
            stack.append((parent,True,True,parent and not won))
            enabled = stack[-1][3]
        elif token == '\\endif':
            if len(command) != 1 or not stack:
                raise ValueError('Unexpected migration endif.')
            parent,_won,_otherwise,_arm = stack.pop()
            enabled = parent
        elif enabled:
            out.append(line)
    if stack:
        raise ValueError('The migration conditional block is not closed.')
    if mode != 'whole' and not saw:
        raise ValueError('An advertised mode needs an explicit migration dispatcher.')
    return '\n'.join(out)+'\n'
