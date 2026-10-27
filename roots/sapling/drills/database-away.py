"""Stop the installed database briefly, prove acceptance refuses, and restore its unchanged launch agent."""

import json
import sys
from pathlib import Path

sys.path.insert(0,str(Path(__file__).resolve().parent))
from drill_support import Places  # noqa: E402
from sapling_outage import database_away  # noqa: E402


def main() -> int:
    try:
        print(json.dumps(database_away(Places.owner())))
        return 0
    except (Exception,KeyboardInterrupt) as error:
        print(json.dumps({'passed':False,'error':str(error)}))
        return 1


if __name__ == '__main__':
    sys.exit(main())
