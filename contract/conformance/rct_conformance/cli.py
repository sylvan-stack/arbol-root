"""The command line of the Root Contract's conformance suite (RCT-4, Interface):

    rct-conformance.py --trunk <command> --root-contract <version> [--only <scenarios>]

It ends with 0 when every scenario passed, 1 when one failed, and 2 when its input was wrong or PostgreSQL's programs
`initdb`, `pg_ctl`, `createdb` and `psql` are missing from the search path, which it names.
"""

from __future__ import annotations

import os
import re
import shlex
import shutil
import signal
import sys
from pathlib import Path
from types import FrameType

from .home import ScenarioHome
from .postgres import PROGRAMS, missing_programs
from .registry import Scenario, select
from .runner import run_suite

CONTRACT = Path(__file__).resolve().parents[2]  # the folder contract/ of the checkout the suite runs from
OPTIONS = ("--trunk", "--root-contract", "--only")
USAGE = ("Usage: rct-conformance.py --trunk <command> --root-contract <version> [--only <scenarios>]\n"
         "  --trunk          what starts the Trunk Build's own program; fixed arguments may follow, quoted as one value\n"
         "  --root-contract  the version of the Root Contract to check, such as 1\n"
         "  --only           only these scenarios, such as R1,R8\n"
         "Exit status: 0 every scenario passed; 1 one failed; 2 wrong input, or PostgreSQL's programs missing.")


class InputError(Exception):
    """Wrong input: the suite ends with 2."""


class Interrupted(BaseException):
    """SIGINT or SIGTERM: the scenario's home is removed and the suite ends with 2. A BaseException, so that no
    scenario takes it for a failure of its own."""


def parse(args: list[str]) -> dict[str, str]:
    values: dict[str, str] = {}
    index = 0
    while index < len(args):
        arg = args[index]
        name, equals, given = arg.partition("=")
        if name not in OPTIONS:
            raise InputError(f"Unknown option: {arg}")
        if equals:
            value: str | None = given
        else:
            index += 1
            value = args[index] if index < len(args) else None
        if value is None or not value.strip() or value.startswith("--"):
            raise InputError(f"Give {name} a value.")
        if name in values:
            raise InputError(f"Give {name} only once.")
        values[name] = value
        index += 1
    for name in ("--trunk", "--root-contract"):
        if name not in values:
            raise InputError(f"Give {name}.")
    return values


def trunk_command(text: str) -> list[str]:
    """The Trunk's command: its program by an absolute path, then any fixed arguments, split without a shell."""
    try:
        words = shlex.split(text)
    except ValueError as error:
        raise InputError(f"--trunk cannot be read: {error}.") from None
    if not words:
        raise InputError("Give --trunk a command.")
    program = words[0]
    if "/" in program:
        path = os.path.abspath(os.path.expanduser(program))
    else:
        found = shutil.which(program)
        if found is None:
            raise InputError(f"The Trunk's program {program} is not on the search path.")
        path = os.path.abspath(found)
    if not os.path.isfile(path) or not os.access(path, os.X_OK):
        raise InputError(f"The Trunk's program {path} does not exist or cannot be run.")
    return [path, *words[1:]]


def layout_file(version: str) -> tuple[int, Path]:
    if not re.fullmatch(r"[1-9][0-9]{0,5}", version):
        raise InputError(f"--root-contract takes a version of the Root Contract, such as 1, not {version}.")
    file = CONTRACT / version / "layout.sql"
    if not file.is_file():
        raise InputError(f"Root Contract version {version} has no layout.sql in {CONTRACT}.")
    return int(version), file


def main(args: list[str]) -> int:
    def out(line: str) -> None:
        print(line, flush=True)

    if args == ["--help"]:
        out(USAGE)
        return 0
    try:
        values = parse(args)
        trunk = trunk_command(values["--trunk"])
        version, layout = layout_file(values["--root-contract"])
        selected = select(values.get("--only"))
        missing = missing_programs()
        if missing:
            raise InputError(f"PostgreSQL's programs are missing from the search path: {', '.join(missing)}. "
                             f"The suite needs {', '.join(PROGRAMS)} of PostgreSQL 17.")
    except (InputError, ValueError) as error:
        print(f"{error}\n{USAGE}", file=sys.stderr, flush=True)
        return 2

    def make_home(scenario: Scenario) -> ScenarioHome:
        return ScenarioHome.create(scenario.id, trunk, version, layout)

    def interrupted(_number: int, _frame: FrameType | None) -> None:
        raise Interrupted()

    for number in (signal.SIGINT, signal.SIGTERM):
        signal.signal(number, interrupted)
    try:
        return run_suite(selected, make_home, out)
    except Interrupted:
        print("The suite was stopped.", file=sys.stderr, flush=True)
        return 2


def entry() -> None:
    sys.exit(main(sys.argv[1:]))
