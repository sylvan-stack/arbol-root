"""The home of one scenario, and the starter (RCT-4, "What it sets up for every scenario").

`ScenarioHome.create` makes, for one scenario:

- a new temporary folder as the Trunk's home;
- a database server of its own in it (postgres.py), listening only on a socket in a short folder under /tmp;
- the Root record `<home>/Library/Application Support/Arbol/roots/rct/root.json`, with `rootContract` set to the
  version under test and `"database": "arbol_rct"`, and the empty folder `exchanges/` beside it, of the mode 0700;
- the database `arbol_rct`, made with `createdb`, and the version's `layout.sql` run on it with `psql`;
- `<home>/.arbol/database.json` with the socket's address, such as `postgresql://rct@%2Ftmp%2Frct-1a2b` (RCT-0);
- the stand-in Driver first on the search path, as `arbol-claude-driver` and `arbol-codex-driver`.

It starts the Trunk Build's own program with `--root rct` and the command, as the launcher does, with only `HOME`,
`PATH`, `LANG` and the test's own variables in its environment, and `close` removes everything again: the Trunk's
process groups and the stand-in's children, the server, its socket folder and the home.
"""

from __future__ import annotations

import json
import os
import select
import shutil
import signal
import subprocess
import sys
import tempfile
import threading
import time
import uuid
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import IO, Any

from .judge import json_lines, parse_line
from .postgres import Held, Server
from .tables import Catalog, catalog, no_table_changed

STANDIN = Path(__file__).resolve().parents[1] / "standin" / "driver.py"
LAUNCHERS = ("arbol-claude-driver", "arbol-codex-driver")
ROOT = "rct"
DATABASE = "arbol_rct"
SYSTEM_PATH = "/usr/bin:/bin:/usr/sbin:/sbin"
LANG = "en_US.UTF-8"
TIME_SCALE = 10  # ARBOL_TEST_TIME_SCALE unless a scenario says otherwise (RCT-4, RCT-D27)
# Every start names the Driver, the Subscription and the model, as Arbol's starts do (ARC-0), so that no scenario
# depends on a Trunk's own settings, of which the test's home has none.
ROUTE = {"driver": "claude", "subscription": "standin", "model": "standin-model"}
START_ANSWER_SECONDS = 20.0  # how long arbol-root waits for the acceptance line (RCT-2)


def iso(moment: datetime | None = None) -> str:
    moment = moment or datetime.now(UTC)
    return moment.strftime("%Y-%m-%dT%H:%M:%S.") + f"{moment.microsecond // 1000:03d}Z"


@dataclass
class Started:
    """A start by the starter: the Exchange it named, the one line it read, and the Trunk's process."""

    exchange: str
    line: str | None  # without its newline; None when the Trunk closed its output or did not answer in time
    answer: Any  # the line as JSON, or None
    process: subprocess.Popen[bytes]
    seconds: float  # from the start to the line


@dataclass
class Completed:
    """A command of the Trunk run to its end, such as `settle` or `run` in the foreground."""

    status: int
    lines: list[str]
    output: list[Any]  # each line as JSON, or None where it is not JSON
    seconds: float


@dataclass
class ScenarioHome:
    scenario: str
    trunk: list[str]
    root_contract: int
    home: Path
    server: Server
    layout: Catalog = field(default_factory=dict)
    created: float = field(default_factory=time.time)
    processes: list[subprocess.Popen[bytes]] = field(default_factory=list)
    exchanges: set[str] = field(default_factory=set)
    chats: set[str] = field(default_factory=set)
    _count: int = 0
    _counting: threading.Lock = field(default_factory=threading.Lock)  # starts may run from several threads at once

    # Making and removing ---------------------------------------------------------------------------------------------

    @classmethod
    def create(cls, scenario: str, trunk: list[str], root_contract: int, layout_file: Path, *,
               python: str | None = None, path: str | None = None) -> ScenarioHome:
        """Makes the scenario's home, server, Root record and database. `path` is where PostgreSQL's programs are
        looked for, the caller's search path unless given; `python` runs the stand-in, this Python unless given."""
        created = time.time()
        home = Path(tempfile.mkdtemp(prefix=f"rct-{scenario.lower()}-"))
        server: Server | None = None
        try:
            for folder in ("standin/bin", "work", "requests", "logs", ".arbol"):
                (home / folder).mkdir(parents=True)
            write_launchers(home / "standin" / "bin", python or os.path.realpath(sys.executable))
            server = Server.create(home / "postgres", home=home, path=path)
            server.createdb(DATABASE)
            server.run_file(DATABASE, layout_file)
            root = home / "Library" / "Application Support" / "Arbol" / "roots" / ROOT
            (root / "exchanges").mkdir(parents=True)
            os.chmod(root / "exchanges", 0o700)
            record = {"root": ROOT, "name": "Root Contract conformance", "status": "working", "createdAt": iso(),
                      "database": DATABASE, "app": "0", "rootContract": root_contract}
            write_json(root / "root.json", record)
            write_json(home / ".arbol" / "database.json", {"address": server.address})
            fixture = cls(scenario, list(trunk), root_contract, home, server, created=created)
            fixture.layout = catalog(server, DATABASE)
            return fixture
        except BaseException:
            if server is not None:
                server.remove()
            shutil.rmtree(home, ignore_errors=True)
            raise

    def close(self) -> None:
        """Ends what the scenario left running, and removes the server, its socket folder and the home."""
        groups = {process.pid for process in self.processes} | set(self.children())
        _kill_groups(groups, self.created)
        for process in self.processes:
            try:
                process.wait(10)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait()
            for stream in (process.stdout, process.stdin):
                if stream is not None:
                    stream.close()
        _wait_until_gone(groups)
        self.server.remove()
        shutil.rmtree(self.home, ignore_errors=True)

    # Paths -----------------------------------------------------------------------------------------------------------

    @property
    def root_folder(self) -> Path:
        return self.home / "Library" / "Application Support" / "Arbol" / "roots" / ROOT

    @property
    def exchanges_folder(self) -> Path:
        return self.root_folder / "exchanges"

    @property
    def work(self) -> Path:
        """The folder the suite starts the Trunk from, unless a scenario names another."""
        return self.home / "work"

    @property
    def standin(self) -> Path:
        return self.home / "standin"

    # The stand-in ----------------------------------------------------------------------------------------------------

    def part(self, name: str = "") -> None:
        """Names the script the stand-in plays from now on: the scenario and its part, such as "R8 tool"."""
        (self.standin / "scenario").write_text(f"{self.scenario} {name}".strip() + "\n", encoding="utf-8")
        (self.standin / "release").unlink(missing_ok=True)

    def release(self) -> None:
        """Lets the runs that the stand-in holds open go on (its `hold()`), until the next part is named."""
        (self.standin / "release").write_text("\n", encoding="utf-8")

    def received(self) -> list[Any]:
        """The stand-in's records, one for each of its starts (RCT-4, StandInRecord)."""
        return json_lines(self.standin / "received.jsonl")

    def children(self) -> list[int]:
        """The children the stand-in started in process groups of their own."""
        return [int(line["pid"]) for line in json_lines(self.standin / "children.jsonl") if isinstance(line, dict)]

    # Starting the Trunk ----------------------------------------------------------------------------------------------

    def environment(self, *, scale: int | None = TIME_SCALE, hang: bool = False,
                    extra: dict[str, str] | None = None) -> dict[str, str]:
        """Only HOME, PATH, LANG and the test's own variables (RCT-4)."""
        env = {"HOME": str(self.home), "PATH": f"{self.standin / 'bin'}:{SYSTEM_PATH}", "LANG": LANG}
        if scale is not None:
            env["ARBOL_TEST_TIME_SCALE"] = str(scale)
        if hang:
            env["ARBOL_TEST_HANG"] = "1"
        env.update(extra or {})
        return env

    def spawn(self, args: list[str], *, cwd: Path | None = None, scale: int | None = TIME_SCALE, hang: bool = False,
              extra: dict[str, str] | None = None, stdin: int | IO[Any] = subprocess.DEVNULL,
              root: str = ROOT) -> subprocess.Popen[bytes]:
        """Starts the Trunk Build's own program with `--root rct`, or the `root` a scenario names, and `args`, in a
        process group of its own (setsid), with its standard output on a pipe and its standard error in the home's
        logs."""
        stderr = (self.home / "logs" / f"trunk-{self._next()}.stderr").open("wb")
        try:
            process = subprocess.Popen([*self.trunk, "--root", root, *args], cwd=cwd or self.work,
                                       env=self.environment(scale=scale, hang=hang, extra=extra), stdin=stdin,
                                       stdout=subprocess.PIPE, stderr=stderr, start_new_session=True)
        finally:
            stderr.close()
        self.processes.append(process)
        return process

    def _next(self) -> int:
        with self._counting:
            self._count += 1
            return self._count

    def request_file(self, request: dict[str, Any]) -> Path:
        file = self.home / "requests" / f"start-{self._next()}.json"
        write_json(file, request)
        return file

    def start(self, message: str | None = "What does build.sh do?", *, exchange: str | None = None,
              request: dict[str, Any] | None = None, options: tuple[str, ...] = (), cwd: Path | None = None,
              scale: int | None = TIME_SCALE, hang: bool = False, extra: dict[str, str] | None = None,
              seconds: float = START_ANSWER_SECONDS, root: str = ROOT,
              meanwhile: Callable[[], None] | None = None) -> Started:
        """Starts `run --detach` as `arbol-root` does (RCT-2): naming the Exchange with `--exchange` and the rest in a
        request file that names the Driver, the Subscription and the model, with standard input from /dev/null; reads
        one line, closes its end of the pipe and removes the request file. `meanwhile` runs once the Trunk is started
        and before its line is read. Starts may run from several threads at once."""
        exchange = exchange or str(uuid.uuid4())
        body: dict[str, Any] = {"route": dict(ROUTE)}
        if message is not None:
            body["message"] = message
        body.update(request or {})
        file = self.request_file(body)
        began = time.monotonic()
        process = self.spawn(["run", "--detach", "--exchange", exchange, "--request", str(file), *options],
                             cwd=cwd, scale=scale, hang=hang, extra=extra, root=root)
        assert process.stdout is not None
        if meanwhile is not None:
            meanwhile()
        line = read_line(process.stdout, seconds)
        took = time.monotonic() - began
        process.stdout.close()
        file.unlink(missing_ok=True)
        answer = parse_line(line)
        self._note(answer)
        return Started(exchange, line, answer, process, took)

    def run(self, args: list[str], *, cwd: Path | None = None, scale: int | None = TIME_SCALE,
            extra: dict[str, str] | None = None, seconds: float = 120.0) -> Completed:
        """Runs a command of the Trunk to its end, such as `settle <exchange>` or `run` in the foreground."""
        began = time.monotonic()
        process = self.spawn(args, cwd=cwd, scale=scale, extra=extra)
        try:
            output, _ = process.communicate(timeout=seconds)
        except subprocess.TimeoutExpired:
            _kill_groups({process.pid}, self.created)
            process.communicate()
            raise
        lines = output.decode("utf-8", "replace").splitlines()
        parsed = [parse_line(line) for line in lines]
        if parsed:
            self._note(parsed[0])
        return Completed(process.returncode, lines, parsed, time.monotonic() - began)

    def ran(self, exchange: str, chat: str | None = None) -> None:
        """Counts an Exchange, and its chat, as run by the scenario, for R16."""
        self.exchanges.add(exchange)
        if chat:
            self.chats.add(chat)

    def _note(self, answer: Any) -> None:
        if isinstance(answer, dict) and answer.get("accepted") is True and isinstance(answer.get("exchange"), str):
            self.ran(answer["exchange"], answer.get("chat") if isinstance(answer.get("chat"), str) else None)

    def stderr(self) -> str:
        """What the Trunk wrote on standard error, for a report of a failure."""
        parts = []
        for log in sorted((self.home / "logs").glob("trunk-*.stderr")):
            text = log.read_text(encoding="utf-8", errors="replace").strip()
            if text:
                parts.append(f"{log.name}: {text[-2000:]}")
        return "\n".join(parts)

    # The Exchange folder ---------------------------------------------------------------------------------------------

    def folders(self, *, hidden: bool = False) -> list[str]:
        """The names in `exchanges/`; without `hidden`, only those that do not start with a dot, as a reader sees."""
        try:
            names = sorted(os.listdir(self.exchanges_folder))
        except FileNotFoundError:
            return []
        return [name for name in names if hidden or not name.startswith(".")]

    def record(self, exchange: str) -> Any:
        """The Exchange's `record.json`, or None when it has no folder."""
        try:
            return json.loads((self.exchanges_folder / exchange / "record.json").read_text(encoding="utf-8"))
        except FileNotFoundError:
            return None

    def events(self, exchange: str) -> list[Any]:
        """The whole lines of the Exchange's `events.jsonl`."""
        return json_lines(self.exchanges_folder / exchange / "events.jsonl")

    def follow(self, exchange: str) -> Follow:
        """Keeps the Exchange's `events.jsonl` open from now on, so that its lines can be read after the Trunk has
        removed the folder."""
        return Follow((self.exchanges_folder / exchange / "events.jsonl").open("rb"))

    def control(self, exchange: str, line: dict[str, Any]) -> None:
        """Appends one line to the Exchange's `control`, as the Root manager and the backend write it (RCT-1.8)."""
        data = (json.dumps(line, separators=(",", ":")) + "\n").encode("utf-8")
        descriptor = os.open(self.exchanges_folder / exchange / "control", os.O_WRONLY | os.O_APPEND)
        try:
            os.write(descriptor, data)
        finally:
            os.close(descriptor)

    # The tables ------------------------------------------------------------------------------------------------------

    def rows(self, query: str) -> list[dict[str, Any]]:
        """The rows of a query on the scenario's database, read with psql."""
        return self.server.rows(DATABASE, query)

    def acceptances_held(self) -> Held:
        """Holds every acceptance until the hold is released: a lock on `chats` that lets rows be read and none be
        written, so that an acceptance's transaction waits at its first statement (RCT-D35)."""
        return self.server.hold(DATABASE, "LOCK TABLE chats IN SHARE MODE")

    def no_table_changed(self) -> None:
        """R16, after the scenario."""
        if not self.server.running():
            self.server.start()
        no_table_changed(self.server, DATABASE, self.layout, self.exchanges, self.chats)


class Follow:
    """An Exchange's `events.jsonl`, held open: what it holds, also once its folder is gone."""

    def __init__(self, stream: IO[bytes]) -> None:
        self.stream = stream
        self.data = b""

    def lines(self) -> list[Any]:
        """The whole lines so far; a last line without a newline is unfinished and skipped (RCT-1.9)."""
        self.data += self.stream.read()
        return [parse_events_line(raw) for raw in self.data.split(b"\n")[:-1]]

    def close(self) -> None:
        self.stream.close()


def parse_events_line(raw: bytes) -> Any:
    text = raw.decode("utf-8", "surrogateescape")
    try:
        return json.loads(text)
    except ValueError:
        return text


def write_json(path: Path, value: Any) -> None:
    path.write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8")
    os.chmod(path, 0o600)


def write_launchers(folder: Path, python: str) -> None:
    """The stand-in under the names of both Drivers' launchers, so that a Trunk finds it first on its search path."""
    for name in LAUNCHERS:
        launcher = folder / name
        launcher.write_text(f"#!/bin/sh\nRCT_STANDIN_AS={name} exec {_quote(python)} -I -B {_quote(str(STANDIN))} "
                            '"$@"\n', encoding="utf-8")
        os.chmod(launcher, 0o755)


def _quote(text: str) -> str:
    return "'" + text.replace("'", "'\\''") + "'"


def read_line(stream: IO[bytes], seconds: float) -> str | None:
    """One line from a pipe, waiting at most `seconds`; None when it closed or nothing whole came in time."""
    descriptor = stream.fileno()
    data = b""
    deadline = time.monotonic() + seconds
    while b"\n" not in data:
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            return None
        ready, _, _ = select.select([descriptor], [], [], remaining)
        if not ready:
            continue
        chunk = os.read(descriptor, 65536)
        if not chunk:
            return None
        data += chunk
    return data.split(b"\n", 1)[0].decode("utf-8", "replace")


def _kill_groups(groups: set[int], since: float) -> None:
    """SIGKILL to each process group that still has a process, when every process in it started after `since`, so
    that a group whose number a program outside the scenario took meanwhile is left alone."""
    members = _processes()
    for group in groups:
        started = [start for _pid, pgid, start in members if pgid == group]
        if started and min(started) >= since - 2:
            try:
                os.killpg(group, signal.SIGKILL)
            except (ProcessLookupError, PermissionError):
                pass


def _wait_until_gone(groups: set[int], seconds: float = 10) -> None:
    deadline = time.monotonic() + seconds
    while time.monotonic() < deadline:
        if not {pgid for _pid, pgid, _start in _processes()} & groups:
            return
        time.sleep(0.05)


def _processes() -> list[tuple[int, int, float]]:
    """Every process of the Mac: its number, its process group, and when it started."""
    output = subprocess.run(["/bin/ps", "-A", "-o", "pid=,pgid=,lstart="], capture_output=True, text=True,
                            check=False, env={"LANG": "C", "LC_ALL": "C", "PATH": SYSTEM_PATH}).stdout
    processes = []
    for line in output.splitlines():
        parts = line.split(None, 2)
        if len(parts) < 3:
            continue
        try:
            start = time.mktime(time.strptime(parts[2].strip(), "%a %b %d %H:%M:%S %Y"))
            processes.append((int(parts[0]), int(parts[1]), start))
        except ValueError:
            continue
    return processes
