"""Entry shared by development and a relocated standalone Build."""

import sys
from pathlib import Path

PACKAGE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PACKAGE / "src"))
from arbol_root.cli import main  # noqa: E402

raise SystemExit(main(package=PACKAGE))
