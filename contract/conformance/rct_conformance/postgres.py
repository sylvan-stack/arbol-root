"""A PostgreSQL server of a test's own (RCT-4, "What it sets up for every scenario").

The server is made with `initdb` in a folder of the test, trusts the role `rct`, and listens only on a socket in a
short folder under /tmp, because the path of a socket may not be longer than 103 bytes. Every program of PostgreSQL
runs with a minimal environment, so that no `PG…` variable, `~/.pgpass` or `~/.psqlrc` of the owner reaches it, and
every connection names the socket's address: nothing here can reach the installed server or a Root in use.
"""

from __future__ import annotations

import json
import os
import re
import shutil
import signal
import subprocess
import tempfile
import time
from pathlib import Path
from typing import Any
from urllib.parse import quote

PROGRAMS = ("initdb", "pg_ctl", "createdb", "psql")
ROLE = "rct"
SOCKET_PATH_LIMIT = 103  # bytes, the longest path of a socket macOS takes
PORT = 5432  # only names the socket file .s.PGSQL.5432 in the server's own folder; no TCP port is opened


class SqlError(Exception):
    """A statement the server refused, with its SQLSTATE, such as 23505."""

    def __init__(self, sqlstate: str | None, message: str) -> None:
        super().__init__(message)
        self.sqlstate = sqlstate


def missing_programs(path: str | None = None) -> list[str]:
    """The programs of PostgreSQL the suite needs that the search path lacks, in the order of PROGRAMS."""
    return [name for name in PROGRAMS if shutil.which(name, path=path) is None]


def programs(path: str | None = None) -> dict[str, str]:
    """Each program of PostgreSQL by its absolute path, found on the search path."""
    found: dict[str, str] = {}
    for name in PROGRAMS:
        location = shutil.which(name, path=path)
        if location is None:
            raise FileNotFoundError(f"PostgreSQL's program {name} is not on the search path.")
        found[name] = os.path.abspath(location)
    return found


def _environment(home: Path) -> dict[str, str]:
    return {"HOME": str(home), "PATH": "/usr/bin:/bin:/usr/sbin:/sbin", "LANG": "en_US.UTF-8",
            "PGCLIENTENCODING": "UTF8"}


class Server:
    """One server: its data folder, its socket folder under /tmp, and the address that reaches it."""

    def __init__(self, data: Path, socket_folder: Path, tools: dict[str, str], home: Path) -> None:
        self.data = data
        self.socket_folder = socket_folder
        self.tools = tools
        self.home = home
        self.log = data.parent / f"{data.name}.log"

    @classmethod
    def create(cls, data: Path, *, home: Path | None = None, path: str | None = None) -> Server:
        """Makes a server in the folder `data`, which must not exist yet, and starts it."""
        tools = programs(path)
        socket_folder = Path(tempfile.mkdtemp(prefix="rct-", dir="/tmp"))
        server = cls(data, socket_folder, tools, home or data.parent)
        try:
            socket = socket_folder / f".s.PGSQL.{PORT}"
            if len(os.fsencode(socket)) > SOCKET_PATH_LIMIT:
                raise RuntimeError(f"The socket path {socket} is longer than {SOCKET_PATH_LIMIT} bytes.")
            server._run([tools["initdb"], "--pgdata", str(data), "--username", ROLE, "--auth", "trust",
                         "--encoding", "UTF8", "--no-locale", "--no-instructions"], timeout=120)
            with (data / "postgresql.conf").open("a", encoding="utf-8") as settings:
                settings.write("\n# The conformance suite's own server: a socket only, in its own folder.\n"
                               "listen_addresses = ''\n"
                               f"unix_socket_directories = '{socket_folder}'\n"
                               f"port = {PORT}\n"
                               "fsync = off\nsynchronous_commit = off\nfull_page_writes = off\n")
            server.start()
        except BaseException:
            server.remove()
            raise
        return server

    @property
    def address(self) -> str:
        """The connection address of `~/.arbol/database.json` (RCT-0), such as postgresql://rct@%2Ftmp%2Frct-1a2b."""
        return f"postgresql://{ROLE}@{quote(str(self.socket_folder), safe='')}"

    def url(self, database: str) -> str:
        return f"{self.address}/{database}"

    def _run(self, command: list[str], *, timeout: float = 60, input_text: str | None = None,
             check: bool = True) -> subprocess.CompletedProcess[str]:
        result = subprocess.run(command, input=input_text, capture_output=True, text=True, timeout=timeout,
                                env=_environment(self.home), cwd=self.home, stdin=None if input_text is not None
                                else subprocess.DEVNULL, check=False)
        if check and result.returncode != 0:
            raise RuntimeError(f"{os.path.basename(command[0])} ended with {result.returncode}: "
                               f"{(result.stderr or result.stdout).strip()}")
        return result

    def start(self) -> None:
        self._run([self.tools["pg_ctl"], "--pgdata", str(self.data), "--log", str(self.log), "--wait",
                   "--timeout", "60", "start"], timeout=90)

    def stop(self, mode: str = "fast") -> None:
        self._run([self.tools["pg_ctl"], "--pgdata", str(self.data), "--mode", mode, "--wait", "--timeout", "60",
                   "stop"], timeout=90)

    def running(self) -> bool:
        if not self.data.is_dir():
            return False
        return self._run([self.tools["pg_ctl"], "--pgdata", str(self.data), "status"], check=False).returncode == 0

    def postmaster_pid(self) -> int | None:
        try:
            return int((self.data / "postmaster.pid").read_text().split("\n", 1)[0])
        except (OSError, ValueError):
            return None

    def createdb(self, name: str) -> None:
        self._run([self.tools["createdb"], "--host", str(self.socket_folder), "--port", str(PORT),
                   "--username", ROLE, name])

    def run_file(self, database: str, file: Path) -> subprocess.CompletedProcess[str]:
        """Runs a file of SQL as `arbol-roots` runs `layout.sql` (RCT-3, RTM-1), and raises on its first error."""
        result = self._run([self.tools["psql"], "--no-psqlrc", "--set", "ON_ERROR_STOP=1", "--set",
                            "VERBOSITY=verbose", "--single-transaction", "--file", str(file.resolve()), self.url(database)],
                           check=False)
        if result.returncode != 0:
            raise _sql_error(result)
        return result

    def execute(self, database: str, sql: str) -> str:
        """Runs statements in one transaction and gives what psql printed, unaligned and without headers."""
        result = self._run([self.tools["psql"], "--no-psqlrc", "--set", "ON_ERROR_STOP=1", "--set",
                            "VERBOSITY=verbose", "--single-transaction", "--quiet", "--no-align", "--tuples-only",
                            "--file", "-", self.url(database)], input_text=sql, check=False)
        if result.returncode != 0:
            raise _sql_error(result)
        return result.stdout

    def value(self, database: str, sql: str) -> Any:
        """The JSON value of one query whose single row and column is json or jsonb."""
        return json.loads(self.execute(database, sql))

    def rows(self, database: str, query: str) -> list[dict[str, Any]]:
        """The rows of a query, each as a JSON object of its columns."""
        rows = self.value(database, f"SELECT coalesce(json_agg(row_to_json(q)), '[]'::json) FROM ({query}) q")
        assert isinstance(rows, list)
        return rows

    def remove(self) -> None:
        """Stops the server, also one that does not answer, and removes its data and socket folders."""
        if self.data.is_dir() and self.running():
            try:
                self.stop("fast")
            except (RuntimeError, subprocess.TimeoutExpired):
                self.stop("immediate")
        pid = self.postmaster_pid()  # still there only when the server did not stop
        if pid is not None:
            _kill_postmaster(pid)
        shutil.rmtree(self.data, ignore_errors=True)
        self.log.unlink(missing_ok=True)
        shutil.rmtree(self.socket_folder, ignore_errors=True)


def _kill_postmaster(pid: int) -> None:
    """Ends a server that pg_ctl could not stop, when the number still belongs to a postgres process."""
    command = subprocess.run(["/bin/ps", "-o", "comm=", "-p", str(pid)], capture_output=True, text=True, check=False)
    if "postgres" not in command.stdout:
        return
    try:
        os.kill(pid, signal.SIGKILL)
    except (ProcessLookupError, PermissionError):
        return
    deadline = time.monotonic() + 10
    while time.monotonic() < deadline:
        try:
            os.kill(pid, 0)
        except (ProcessLookupError, PermissionError):
            return
        time.sleep(0.05)


_SQLSTATE = re.compile(r"(?:ERROR|FATAL):\s+([0-9A-Z]{5}):")


def _sql_error(result: subprocess.CompletedProcess[str]) -> SqlError:
    text = (result.stderr or result.stdout).strip()
    match = _SQLSTATE.search(text)
    return SqlError(match.group(1) if match else None, text or f"psql ended with {result.returncode}")
