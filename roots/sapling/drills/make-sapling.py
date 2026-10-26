"""Make First Sapling once, using only merged manager code; refuse an existing Root."""

import json
import sys
from pathlib import Path

sys.path.insert(0,str(Path(__file__).resolve().parent))
from drill_support import Places  # noqa: E402
from sapling_creation import make_sapling  # noqa: E402


def main() -> int:
    try:
        places = Places.owner()
        source = places.home/'repos/sylvan-stack/readonly/arbol-root'
        print(json.dumps(make_sapling(places,source)))
        return 0
    except Exception as error:
        print(json.dumps({'passed':False,'error':str(error)}))
        return 1


if __name__ == '__main__':
    sys.exit(main())
