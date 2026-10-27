"""Run the named installed First Sapling stopping drill only with --run."""

import sys
from pathlib import Path

sys.path.insert(0,str(Path(__file__).resolve().parent))
from stopping_drills import entry  # noqa: E402

if __name__ == "__main__":
    sys.exit(entry('root-killed-while-forcing'))
