# Shared fixtures; case bodies live in top/ and mid/. See TESTS.md.
from __future__ import annotations
import subprocess


import json
import os
import shutil
import sys
import tarfile
import tempfile
import unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from scripts.build import copy_layout  # noqa: E402
from scripts.package_build import archive, package  # noqa: E402
from scripts.package_support import digest, metadata, target, verify, write_manifest  # noqa: E402

from scripts.package_support import digest, target  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]


class Package(unittest.TestCase):
    def setUp(self) -> None:
        temporary = tempfile.TemporaryDirectory(prefix='rtm-package-')
        self.addCleanup(temporary.cleanup)
        self.base = Path(temporary.name).resolve()
        self.source, self.folder = self.base / 'source', self.base / 'package'
        self.source.mkdir()
        self.folder.mkdir()
        for name in ['src','scripts','tests','bin','contract','roots']:
            shutil.copytree(ROOT / name, self.source / name, ignore=shutil.ignore_patterns('__pycache__','*.pyc'))
        for name in ['package.json','pyproject.toml','.python-version','uv.lock','arbol-build.json','README.md']:
            shutil.copy2(ROOT / name, self.source / name)
        self.cache = self.base / 'cache'
        self.cache.mkdir()
        runtime = self.base / 'fake/python/bin'
        runtime.mkdir(parents=True)
        interpreter = runtime / 'python3.14'
        interpreter.write_text('#!/bin/sh\nif [ -n "$PACKAGE_REPORT" ]; then\n'
                               '  printf "%s\\n" "$$" "$@" > "$PACKAGE_REPORT"\nelse\n  echo 3.14.8\nfi\n')
        interpreter.chmod(0o755)
        compressed = self.cache / 'fake.tar.gz'
        with tarfile.open(compressed, 'w:gz') as bundle:
            bundle.add(runtime.parent, arcname='python')
        checksum = digest(compressed)
        compressed.rename(self.cache / (checksum+'.tar.gz'))
        pin = json.loads((self.source / 'scripts/python-distribution.json').read_text())
        pin['distributions'][target()]['sha256'] = checksum
        (self.source / 'scripts/python-distribution.json').write_text(json.dumps(pin))
        patch = mock.patch.dict(os.environ, {'ARBOL_PYTHON_ARCHIVE_CACHE':str(self.cache)})
        patch.start()
        self.addCleanup(patch.stop)


# Archived complete imports; restore needed names in their original scope, not at this file tail.
