#!/usr/bin/env python3
"""Explicit Jensen migration qualification; default is preview only."""

import sys
from pathlib import Path

sys.path.insert(0,str(Path(__file__).resolve().parent))
from migration_drills import entry  # noqa: E402

if __name__ == '__main__':
    raise SystemExit(entry('open-exchange'))
