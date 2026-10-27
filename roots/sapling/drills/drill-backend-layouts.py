"""Guarded installed backend schema acceptance; preview without --run."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from backend_layout_drills import entry  # noqa: E402

if __name__ == "__main__":
    raise SystemExit(entry())
