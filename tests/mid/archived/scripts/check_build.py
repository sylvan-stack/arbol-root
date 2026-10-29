"""Run the top-tier tests with this image's interpreter."""

from __future__ import annotations
import subprocess


import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts.package_support import verify  # noqa: E402



def main() -> int:
    try:
        verify(ROOT)
        python = ROOT / 'runtime/python/bin/python3.14'
        # A Build runs the top tier only (SYL-329); the mid tier runs only when the owner asks.
        result = subprocess.run([str(python), '-I', '-B', '-m', 'unittest', 'discover', '-s', 'tests/top', '-t', 'tests', '-v'],
                                cwd=ROOT, check=False)
        if result.returncode:
            return 1
        verify(ROOT)
    except (OSError, ValueError, KeyError) as error:
        print(f'Root Build unit check failed: {error}', file=sys.stderr)
        return 1
    return 0


if __name__ == '__main__':
    raise SystemExit(main())

# Archived complete imports; restore needed names in their original scope, not at this file tail.
