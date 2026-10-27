#!/usr/bin/env python3
"""Explicitly create Jensen Root and qualify its merged-source manager; default is preview only."""

import sys
from pathlib import Path

sys.path.insert(0,str(Path(__file__).resolve().parent))
from jensen_creation import entry  # noqa: E402

if __name__ == '__main__':
    raise SystemExit(entry())
