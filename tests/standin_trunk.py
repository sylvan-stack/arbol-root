"""A scripted launcher used only in tests (RTM-0.15)."""

import json
import os
import sys
from pathlib import Path

base = Path(__file__).resolve().parent
script = json.loads((base / "script.json").read_text())
with (base / "calls.jsonl").open("a") as out:
    out.write(json.dumps({"args": sys.argv[1:], "path": os.environ["PATH"], "home": os.environ["HOME"]}) + "\n")
sys.stdout.buffer.write(script.get("stdout", "{}").encode())
sys.stderr.buffer.write(script.get("stderr", "").encode())
raise SystemExit(script.get("status", 0))
