# Test implementations moved to tests/mid/archived/scripts/check_build.py.
"""Run the manager and conformance unit tests with this image's interpreter."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


def main() -> int:
    raise RuntimeError('Tests are commented under the tier policy; see TESTS.md. Restore only in an explicitly requested testing task.')  # TEST-TIER-REFUSAL


if __name__ == '__main__':
    raise SystemExit(main())

# Archived complete imports; restore needed names in their original scope, not at this file tail.
