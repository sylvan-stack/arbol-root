"""Preflight two Haiku messages; --send explicitly spends two of the shared allowance."""

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0,str(Path(__file__).resolve().parent))
from drill_support import Places  # noqa: E402
from sapling_messages import real_messages  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--send',action='store_true')
    args = parser.parse_args()
    try:
        print(json.dumps(real_messages(Places.owner(),send=args.send)))
        return 0
    except Exception as error:
        print(json.dumps({'passed':False,'error':str(error)}))
        return 1


if __name__ == '__main__':
    sys.exit(main())
