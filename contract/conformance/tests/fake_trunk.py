"""A fake Trunk for the suite's own tests: it is no Trunk, and checks nothing of the Root Contract.

Started by the suite as a Trunk Build's program would be, `fake_trunk.py --root rct <command> …`. It writes what it
was given to `<home>/fake-trunk.json` and answers with an acceptance line. FAKE_TRUNK_MODE says what else it does:

- `report`: nothing else;
- `accept`: writes the chat, the open Exchange and the message at position 0 of the Exchange it was given;
- `change-layout`: also adds a table, a column and an index;
- `foreign-row`: also writes a chat and an Exchange that its acceptance line does not name;
- `linger`: starts a child in its process group, and both wait for an hour;
- `standin`: runs the Driver it finds on its search path, `arbol-claude-driver run --control --request <file>`, and
  keeps the events in `<home>/fake-standin.jsonl`.

`settle <exchange>` answers `{"exchange": …, "settled": "none"}`. FAKE_PSQL names psql for the modes that write rows.
The fixed command argument `--refuse` refuses every command immediately, for testing whole-suite failure reporting.
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import time
import uuid
from pathlib import Path
from typing import Any

HOME = Path(os.environ["HOME"])


def option(args: list[str], name: str) -> str | None:
    return args[args.index(name) + 1] if name in args else None


def psql(sql: str) -> None:
    address = json.loads((HOME / ".arbol" / "database.json").read_text())["address"]
    root = json.loads((HOME / "Library/Application Support/Arbol/roots/rct/root.json").read_text())
    subprocess.run([os.environ["FAKE_PSQL"], "--no-psqlrc", "--set", "ON_ERROR_STOP=1", "--quiet", "--command", sql,
                    f"{address}/{root['database']}"], check=True, env={"PATH": "/usr/bin:/bin", "HOME": str(HOME)},
                   stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL)


def accept(exchange: str, chat: str) -> None:
    psql("BEGIN;"
         f"INSERT INTO chats (id, created_at) VALUES ('{chat}', now());"
         f"INSERT INTO exchanges (id, chat_id, number, state, trunk, build, route, working_folder, accepted_at)"
         f" VALUES ('{exchange}', '{chat}', 1, 'open', 'fake', '0', '{{\"driver\": \"claude\"}}', '{os.getcwd()}',"
         " now());"
         f"INSERT INTO messages VALUES ('{exchange}', 0, 'user', 'What does build.sh do?');"
         "COMMIT;")


def main(args: list[str]) -> int:
    if args[:1] == ["--refuse"]:
        print(json.dumps({"error": {"code": "trunk_failed", "message": "The test Trunk refuses this command."}}))
        return 1
    mode = os.environ.get("FAKE_TRUNK_MODE", "report")
    command = args[2] if len(args) > 2 else ""
    if command == "settle":
        print(json.dumps({"exchange": args[3], "settled": "none"}))
        return 0
    file = option(args, "--request")
    request: Any = json.loads(Path(file).read_text()) if file else None
    stdin = os.fstat(0)
    devnull = os.stat("/dev/null")
    report = {"arguments": args, "environment": dict(os.environ), "workingDirectory": os.getcwd(),
              "pid": os.getpid(), "sid": os.getsid(0), "pgid": os.getpgid(0),
              "stdinIsDevNull": (stdin.st_rdev, stdin.st_ino) == (devnull.st_rdev, devnull.st_ino),
              "request": request, "driver": shutil.which("arbol-claude-driver"),
              "codexDriver": shutil.which("arbol-codex-driver")}
    (HOME / "fake-trunk.json").write_text(json.dumps(report))
    exchange = option(args, "--exchange") or str(uuid.uuid4())
    chat = str(uuid.uuid4())
    if mode in ("accept", "change-layout", "foreign-row"):
        accept(exchange, chat)
    if mode == "change-layout":
        psql("CREATE TABLE extra (id integer); ALTER TABLE chats ADD COLUMN extra text;"
             " CREATE INDEX messages_by_text ON messages (text);")
    if mode == "foreign-row":
        accept(str(uuid.uuid4()), str(uuid.uuid4()))
    if mode == "standin":
        run_request = HOME / "run-1.json"
        run_request.write_text(json.dumps({"runId": f"{exchange}.1", "tools": "all", "input": {
            "role": "user", "text": request["message"]}, "workingDirectory": os.getcwd(), "labels": {"x": "1"}}))
        with (HOME / "fake-standin.jsonl").open("wb") as events:
            standin = subprocess.Popen(["arbol-claude-driver", "run", "--control", "--request", str(run_request)],
                                       stdin=subprocess.PIPE, stdout=events)
            standin.wait(60)
    print(json.dumps({"accepted": True, "duplicate": False, "root": "rct", "exchange": exchange, "chat": chat,
                      "number": 1, "trunk": "fake", "build": "0"}), flush=True)
    if mode == "foreground":
        print('{"n":1,"event":{"type":"text","text":"kept after acceptance"}}', flush=True)
    if mode == "linger":
        subprocess.Popen(["/bin/sleep", "3600"])
        time.sleep(3600)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
