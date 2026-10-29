# Shared fixtures; case bodies live in top/ and mid/. See TESTS.md.
from __future__ import annotations


import json
import os
import shlex
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from arbol_root.model import identity  # noqa: E402


REPO = Path(__file__).resolve().parents[1]


class Commands(unittest.TestCase):
    def setUp(self) -> None:
        temporary = tempfile.TemporaryDirectory(prefix="rtm-command-")
        self.addCleanup(temporary.cleanup)
        self.home = Path(temporary.name)
        self.development = self.home / 'development'
        self.development.mkdir()
        for name in ['src', 'bin']:
            shutil.copytree(REPO / name, self.development / name, ignore=shutil.ignore_patterns('__pycache__'))
        shutil.copy2(REPO / 'package.json', self.development / 'package.json')
        self.root_dir = self.home / "private root"
        self.root_dir.mkdir()
        (self.root_dir / "root.json").write_text('{"root":"sapling"}')
        self.bin_dir = self.home / "private bin"
        self.bin_dir.mkdir()
        script = self.bin_dir / "arbol-trunk"
        shutil.copy2(REPO / 'tests/standin_trunk.py', self.bin_dir / 'standin_trunk.py')
        script.write_text('#!/bin/sh\nexec '+shlex.quote(sys.executable)+' -I -B '+
                          shlex.quote(str(self.bin_dir / 'standin_trunk.py'))+' "$@"\n')
        script.chmod(0o755)
        self.script(stdout='  { "root": "sapling", "trunks": [], "extra": "🌲" }\n')
        self.common = ['--root', 'sapling', '--root-dir', str(self.root_dir), '--bin-dir', str(self.bin_dir)]

    def script(self, **values: object) -> None:
        (self.bin_dir / "script.json").write_text(json.dumps(values))

    def run_cli(self, args: list[str], *, package: Path | None = None) -> subprocess.CompletedProcess[bytes]:
        package = package or self.development
        return subprocess.run([sys.executable, '-I', '-B', str(package / 'bin/entry.py'), *args],
                              env={**os.environ, 'HOME': str(self.home), 'ARBOL_BUILD_DIR': '/wrong',
                                   'ARBOL_BUILD_NUMBER': 'ffff'}, capture_output=True, check=False, timeout=10)

    def refusal(self, args: list[str], code: str, *, package: Path | None = None) -> None:
        reply = self.run_cli(args, package=package)
        self.assertEqual(reply.returncode, 1, reply)
        self.assertEqual(json.loads(reply.stdout)['error']['code'], code, reply)


# Archived complete imports; restore needed names in their original scope, not at this file tail.
