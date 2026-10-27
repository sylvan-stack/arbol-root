"""Preview one installed Jensen stale/reimport phase; --run explicitly applies it."""

import sys
from pathlib import Path

sys.path.insert(0,str(Path(__file__).resolve().parent))
from chat_reimport_drills import entry  # noqa: E402

if __name__=='__main__':
    sys.exit(entry())
