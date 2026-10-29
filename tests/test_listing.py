# Shared fixtures only; test bodies are in top/ and mid/. See TESTS.md.
from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))

from arbol_root.model import Identity  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
AT = '2026-10-26T09:00:00.000Z'
CHAT = 'c3d4e5f6-0718-4293-a4b5-c6d7e8f90a1b'


def record(number: int, *, root: str = 'sapling', pid: int = 123, accepted: bool = True, ended: bool = False) -> dict[str, Any]:
    value = {'rootContract':1,'root':root,'exchange':f'00000000-0000-4000-8000-{number:012d}',
             'chat':CHAT,'trunk':'trivial','build':'a','process':{'pid':pid,'startedAt':AT},
             'signsOfLife':{'heartbeat':41,'waitingFor':'tool','since':AT}}
    if accepted:
        value['acceptedAt'] = AT
    if ended:
        value['end'] = {'state':'completed','at':AT}
    return value


class Listing(unittest.TestCase):
    def setUp(self) -> None:
        temporary = tempfile.TemporaryDirectory(prefix='rtm-list-')
        self.addCleanup(temporary.cleanup)
        self.base = Path(temporary.name).resolve()
        self.root = self.base / 'root'
        self.root.mkdir()
        (self.root / 'root.json').write_text('{"root":"sapling"}')
        self.catalogue = self.root / 'exchanges'
        self.catalogue.mkdir()
        self.context = Identity('sapling','7','1.0.0',self.root,self.base / 'no-launcher')

    def put(self, value: dict[str, Any]) -> Path:
        folder = self.catalogue / str(value['exchange'])
        folder.mkdir(exist_ok=True)
        (folder / 'record.json').write_text(json.dumps(value))
        return folder


class ProcessIdentity(unittest.TestCase):
    pass  # TEST-TIER-EMPTY-SUITE; helpers remain importable.


# Archived complete imports; restore needed names in their original scope, not at this file tail.
