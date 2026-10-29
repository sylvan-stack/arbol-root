"""Run the manager and conformance unit tests with this image's interpreter."""

from __future__ import annotations
import subprocess


import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts.package_support import verify  # noqa: E402



def main() -> int:
    print('SYL-327 reduced the retained test selection. Full Build qualification requires an explicitly requested review of the qualification map; see TESTS.md.', file=sys.stderr)
    return 1
    try:
        verify(ROOT)
        python = ROOT / 'runtime/python/bin/python3.14'
        for start, top in [('tests', 'tests'), ('contract/conformance/tests', 'contract/conformance')]:
            result = subprocess.run([str(python), '-I', '-B', '-m', 'unittest', 'discover', '-s', start, '-t', top, '-v'],
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
