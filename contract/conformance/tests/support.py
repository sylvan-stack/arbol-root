"""What the suite's own tests share. They run from the checkout:

    uv run --no-sync python -B -m unittest discover -s contract/conformance/tests -t contract/conformance

Every test makes its servers with initdb in temporary folders, reached only through sockets under /tmp, as the
suite does; none reaches the installed server or a Root in use.
"""

from __future__ import annotations

import shutil
import sys
from pathlib import Path

CONFORMANCE = Path(__file__).resolve().parents[1]
CONTRACT = CONFORMANCE.parent
LAYOUT = CONTRACT / "1" / "layout.sql"
CLI = CONFORMANCE / "bin" / "rct-conformance.py"
FAKE_TRUNK = [sys.executable, "-I", "-B", str(CONFORMANCE / "tests" / "fake_trunk.py")]
EMBEDDED_SPECIFICATION = CONFORMANCE / "specifications" / "03-the-chat-tables.md"
SPECIFICATION = (EMBEDDED_SPECIFICATION if EMBEDDED_SPECIFICATION.is_file()
                 else Path.home() / "Artifacts/arbol-root/contract/03-the-chat-tables.md")


def psql() -> str:
    found = shutil.which("psql")
    assert found is not None, "psql is not on the search path"
    return found
