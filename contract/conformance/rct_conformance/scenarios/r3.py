"""R3: refusals (RCT-4).

An unknown option, no message, a Root identifier that is not one word, such as `../rct`, an unknown Root, a version not
in the Build's list, a working folder that is relative or missing, a busy chat, `--replaces` with a message, a stopped
database server. The suite judges: one error line with the code of RCT-2, the exit status 1, within 15 seconds; no
folder, no row, and the stand-in never started.

Covers RCT-0.3, 0.5, 2.2, 2.13 and 2.17.
"""

from __future__ import annotations

import os
import select
import subprocess
import time
import uuid
from pathlib import Path
from typing import IO, Any

from ..home import ROOT, ROUTE, ScenarioHome
from ..judge import check, equal, parse_line, wait_until
from .r1 import END_SECONDS, accepted

MESSAGE = "What does build.sh do?"
ANSWER_SECONDS = 15.0  # RCT-2: the Trunk answers within 15 seconds of its start, accepted or refused
EXIT_SECONDS = 5.0  # after its answer, for the Trunk's process to end
UNKNOWN_ROOT = "unknown"
VERSION_NO_BUILD_LISTS = 1000  # added to the version under test


# TEST-TIER-DISABLED-BEGIN contract/conformance/rct_conformance/scenarios/r3.py::run
# def run(home: ScenarioHome) -> None:
#     refused(home, "option", "invalid_input", options=("--bogus",))
#     refused(home, "no message", "invalid_input", message=None)
#     refused(home, "root", "invalid_input", root="../rct")
#     refused(home, "relative folder", "invalid_input", options=("--cwd", "."))
#     refused(home, "missing folder", "invalid_input", request={"workingFolder": str(home.home / "missing")})
#     refused(home, "replaces", "invalid_input", request={"replaces": str(uuid.uuid4())})
#     refused(home, "unknown root", "unknown_root", root=UNKNOWN_ROOT)
#     record_file = home.root_folder / "root.json"
#     record = json.loads(record_file.read_text(encoding="utf-8"))
#     write_json(record_file, {**record, "rootContract": home.root_contract + VERSION_NO_BUILD_LISTS})
#     try:
#         refused(home, "version", "contract_mismatch")
#     finally:
#         write_json(record_file, record)
#     busy_chat(home)
#     refused(home, "database away", "database_unavailable", database_away=True)
# TEST-TIER-DISABLED-END contract/conformance/rct_conformance/scenarios/r3.py::run
def run(home: ScenarioHome) -> None:
    raise RuntimeError('Tests are commented under the tier policy; see TESTS.md. Restore only in an explicitly requested testing task.')  # TEST-TIER-REFUSAL


def busy_chat(home: ScenarioHome) -> None:
    """A second message to a chat whose Exchange is open, while the stand-in holds that Exchange's run open: refused
    with `chat_busy`, naming the open Exchange; then the open one goes on to its end."""
    home.part("busy")
    first = home.start(MESSAGE)
    chat = accepted(first)["chat"]
    wait_until(lambda: home.events(first.exchange), END_SECONDS, "the open Exchange's first event")
    message = refused(home, "busy", "chat_busy", request={"chat": chat})
    check(first.exchange in message, "busy: the refusal does not name the open Exchange.", first.exchange, message)
    home.release()
    wait_until(lambda: first.exchange not in home.folders(hidden=True), END_SECONDS,
               "busy: the open Exchange's folder to go")
    equal(home.rows(f"SELECT state FROM exchanges WHERE chat_id = '{chat}'"), [{"state": "completed"}],
          "busy: the Exchanges of the chat")
    equal(len([record for record in home.received() if record.get("part") == "busy"]), 1,
          "busy: the starts of the stand-in")


def refused(home: ScenarioHome, part: str, code: str, *, message: str | None = MESSAGE,
            request: dict[str, Any] | None = None, options: tuple[str, ...] = (), root: str = ROOT,
            database_away: bool = False) -> str:
    """Starts `run --detach` as the starter does, naming the Exchange, and judges one refusal with `code`: one error
    line, the exit status 1, within 15 seconds, no folder, no row, and the stand-in never started. With
    `database_away`, the database server is stopped for the start. Gives the refusal's message."""
    home.part(part)
    exchange = str(uuid.uuid4())
    body: dict[str, Any] = {"route": dict(ROUTE)}
    if message is not None:
        body["message"] = message
    body.update(request or {})
    file = home.request_file(body)
    folders = listing(home.home / "Library" / "Application Support" / "Arbol")
    counts = row_counts(home)
    if database_away:
        home.server.stop()
    try:
        began = time.monotonic()
        process = home.spawn(["run", "--detach", "--exchange", exchange, "--request", str(file), *options],
                             root=root)
        assert process.stdout is not None
        lines, seconds = read_lines(process.stdout, ANSWER_SECONDS)
        status = ended(process, began + ANSWER_SECONDS + EXIT_SECONDS)
    finally:
        if database_away:
            home.server.start()
    file.unlink(missing_ok=True)

    check(len(lines) == 1, f"{part}: the Trunk did not answer with one line.", "one error line", lines)
    answer = parse_line(lines[0])
    error = answer.get("error") if isinstance(answer, dict) else None
    check(isinstance(answer, dict) and list(answer) == ["error"] and isinstance(error, dict)
          and sorted(error) == ["code", "message"] and isinstance(error["message"], str) and error["message"],
          f"{part}: the answer is no refusal of RCT-2.", '{"error":{"code":…,"message":…}}', lines[0])
    assert isinstance(error, dict)
    equal(error["code"], code, f"{part}: the code of the refusal")
    check(seconds is not None and seconds < ANSWER_SECONDS, f"{part}: the refusal came after {seconds} s.",
          f"within {ANSWER_SECONDS:g} s", seconds)
    equal(status, 1, f"{part}: the exit status of the refusal")
    equal(listing(home.home / "Library" / "Application Support" / "Arbol"), folders,
          f"{part}: the folders of the Roots after the refusal")
    equal(row_counts(home), counts, f"{part}: the number of chats and Exchanges after the refusal")
    for table in ("exchanges", "messages", "tool_calls", "runs"):
        column = "id" if table == "exchanges" else "exchange_id"
        equal(home.rows(f"SELECT 1 AS found FROM {table} WHERE {column} = '{exchange}'"), [],
              f"{part}: the rows of the refused Exchange in {table}")
    # A start of the stand-in records itself when it ends; one that still runs is in the Trunk's process group. In the
    # part "busy", the open Exchange's run is held, so it has no record yet.
    equal([record for record in home.received() if record.get("part") == part], [],
          f"{part}: the starts of the stand-in")
    check(not group_alive(process.pid), f"{part}: a process of the Trunk's group lives on after the refusal.")
    message_text: str = error["message"]
    return message_text


def read_lines(stream: IO[bytes], seconds: float) -> tuple[list[str], float | None]:
    """The whole lines the Trunk writes until it closes its output, waiting at most `seconds`, and how long the first
    took."""
    descriptor = stream.fileno()
    data = b""
    began = time.monotonic()
    first: float | None = None
    deadline = began + seconds
    while True:
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            break
        ready, _, _ = select.select([descriptor], [], [], remaining)
        if not ready:
            continue
        chunk = os.read(descriptor, 65536)
        if not chunk:
            break
        data += chunk
        if first is None and b"\n" in data:
            first = time.monotonic() - began
    stream.close()
    return [line.decode("utf-8", "replace") for line in data.split(b"\n")[:-1]], first


def ended(process: subprocess.Popen[bytes], deadline: float) -> int | None:
    """The exit status of the Trunk, or None when it has not ended by `deadline`."""
    try:
        return process.wait(max(deadline - time.monotonic(), 0.1))
    except subprocess.TimeoutExpired:
        return None


def listing(folder: Path) -> list[str]:
    """The folders and files under `folder` down to the Exchange folders, `roots/<root>/exchanges/<name>`, as paths
    relative to it; what an Exchange folder holds changes while its Exchange runs."""
    paths = (path.relative_to(folder) for path in folder.rglob("*"))
    return sorted(str(path) for path in paths if len(path.parts) <= 4)


def row_counts(home: ScenarioHome) -> dict[str, Any]:
    rows = home.rows("SELECT (SELECT count(*) FROM chats) AS chats, (SELECT count(*) FROM exchanges) AS exchanges")
    return rows[0]


def group_alive(pgid: int) -> bool:
    try:
        os.killpg(pgid, 0)
    except ProcessLookupError:
        return False
    except PermissionError:
        return True
    return True

# Archived complete imports; restore needed names in their original scope, not at this file tail.
# TEST-TIER-IMPORTS-BEGIN contract/conformance/rct_conformance/scenarios/r3.py:13
# import json
# TEST-TIER-IMPORTS-END contract/conformance/rct_conformance/scenarios/r3.py:13
# TEST-TIER-IMPORTS-BEGIN contract/conformance/rct_conformance/scenarios/r3.py:22
# from ..home import ROOT, ROUTE, ScenarioHome, write_json
# TEST-TIER-IMPORTS-END contract/conformance/rct_conformance/scenarios/r3.py:22
