# Shared fixtures only; test bodies are in top/ and mid/. See TESTS.md.
from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


class SqlSupport(unittest.TestCase):
    @staticmethod
    def image(base: Path, *, older: str | None = None) -> Path:
        folder = base / 'image'
        folder.mkdir()
        (folder / 'package.json').write_text('{"version":"1.0.0"}')
        (folder / 'build.json').write_text(json.dumps({'component':'arbol-root','root':'fictionalnew',
                                                      'build':'1','entry':'bin/arbol-root','packageVersion':'1.0.0'}))
        (folder / 'package-manifest.json').write_text(json.dumps({'layout':{
            'root':'fictionalnew','rootContract':1,'grewFrom':older}}))
        (folder / 'layout').mkdir()
        for name in ['chat-tables.sql','root-tables.sql', *(['migrate.sql'] if older else [])]:
            (folder / 'layout' / name).write_text('-- fictional input\n')
        return folder


# Archived complete imports; restore needed names in their original scope, not at this file tail.
