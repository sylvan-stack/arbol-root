"""A development image for fictional CLI Roots, independent of the enclosing Build."""

from __future__ import annotations

import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def development(base: Path) -> Path:
    folder = base / 'development'
    folder.mkdir()
    for name in ['src','bin']:
        shutil.copytree(ROOT / name,folder / name,ignore=shutil.ignore_patterns('__pycache__','*.pyc'))
    shutil.copy2(ROOT / 'package.json',folder / 'package.json')
    return folder
