"""Root-owned SQL check inputs and a disposable socket-only PostgreSQL server."""

from __future__ import annotations

import os
import shutil
import stat
import subprocess
import sys
import tempfile
from collections.abc import Iterator
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))
sys.path.insert(0, str(ROOT / 'contract/conformance'))
from rct_conformance.postgres import PORT, ROLE, Server, programs  # noqa: E402

from arbol_root.model import build_record, identifier, object_file  # noqa: E402
from scripts.migration_modes import FILE as MODES_FILE  # noqa: E402
from scripts.migration_modes import read_modes  # noqa: E402


def regular(path: Path) -> Path:
    if not stat.S_ISREG(path.lstat().st_mode):
        raise ValueError(f'Required SQL input is not a regular file: {path}')
    return path


@dataclass(frozen=True)
class BuildInput:
    folder: Path
    root: str
    number: str
    contract: int
    older: str | None
    modes: tuple[str, ...] = ()

    @classmethod
    def read(cls, folder: Path) -> BuildInput:
        record = build_record(folder)
        layout = object_file(folder / 'package-manifest.json').get('layout')
        if (not isinstance(layout, dict) or layout.get('root') != record['root']
                or type(layout.get('rootContract')) is not int or layout['rootContract'] < 1):
            raise ValueError('The copied-layout manifest must match this numbered Root Build.')
        older = layout.get('grewFrom')
        if older is not None and (not identifier(older) or older == record['root']):
            raise ValueError('The copied lineage must name a different valid Root.')
        for name in ['chat-tables.sql', 'root-tables.sql', *(['migrate.sql'] if older is not None else [])]:
            regular(folder / 'layout' / name)
        modes: tuple[str, ...] = ()
        if 'migrationModes' in layout:
            capability = read_modes(folder / 'layout' / MODES_FILE)
            if older is None or capability != layout['migrationModes']:
                raise ValueError('The advertised migration modes do not match copied capabilities/lineage.')
            assert capability is not None
            modes = tuple(capability['modes'])
        return cls(folder, record['root'], record['build'], layout['rootContract'], older, modes)

    def file(self, name: str) -> Path:
        return regular(self.folder / 'layout' / name)


def tools(path: str) -> dict[str, str]:
    found = programs(path)
    dump = shutil.which('pg_dump', path=path)
    if dump is None:
        raise FileNotFoundError("PostgreSQL's program pg_dump is not on the search path.")
    return {**found, 'pg_dump':os.path.abspath(dump)}


@dataclass
class SqlLab:
    server: Server
    tools: dict[str, str]
    environment: dict[str, str]
    restrict_key: bool

    def run(self, program: str, arguments: list[str], *, cwd: Path | None = None,
            check: bool = True, input_text: str | None = None) -> subprocess.CompletedProcess[str]:
        answer = subprocess.run([self.tools[program], *arguments], env=self.environment,
                                cwd=cwd or self.server.home, capture_output=True, text=True, encoding='utf-8',
                                stdin=None if input_text is not None else subprocess.DEVNULL,
                                input=input_text, check=False, timeout=60)
        if check and answer.returncode:
            raise RuntimeError(f'{program} ended with {answer.returncode}: {(answer.stderr or answer.stdout).strip()}')
        return answer

    def run_file(self, database: str, file: Path, *, variables: dict[str, str] | None = None,
                 cwd: Path | None = None, single: bool = True, check: bool = True) -> subprocess.CompletedProcess[str]:
        args = ['--no-psqlrc', '--set', 'ON_ERROR_STOP=1']
        if single:
            args.append('--single-transaction')
        for key, value in (variables or {}).items():
            args += ['--set', key+'='+value]
        args += ['--file', str(regular(file).resolve()), self.server.url(database)]
        return self.run('psql', args, cwd=cwd, check=check)

    def dump(self, database: str) -> str:
        args = ['--host', str(self.server.socket_folder), '--port', str(PORT), '--username', ROLE,
                '--schema-only', '--no-owner', '--no-privileges']
        if self.restrict_key:
            args.append('--restrict-key=ArbolLayoutCheck')
        return self.run('pg_dump', [*args, database]).stdout


@contextmanager
def private_server(*, path: str | None = None) -> Iterator[SqlLab]:
    search = os.environ.get('PATH', os.defpath) if path is None else path
    found = tools(search)
    with tempfile.TemporaryDirectory(prefix='root-sql-check-') as temporary:
        home = Path(temporary).resolve()
        server = Server.create(home / 'postgres', home=home, path=search)
        try:
            environment = {'HOME':str(home), 'PATH':search, 'LANG':'en_US.UTF-8'}
            lab = SqlLab(server, found, environment, False)
            lab.restrict_key = '--restrict-key' in lab.run('pg_dump', ['--help']).stdout
            yield lab
        finally:
            server.remove()
