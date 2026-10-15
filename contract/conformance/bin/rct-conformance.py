"""rct-conformance: the Root Contract's conformance suite (RCT-4). Started with Python 3.14 as
`python3.14 contract/conformance/bin/rct-conformance.py --trunk <command> --root-contract <version> [--only <ids>]`."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from rct_conformance.cli import entry  # noqa: E402

entry()
