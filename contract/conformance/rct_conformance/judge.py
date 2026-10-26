"""What a scenario judges with (RCT-4.2): what the Trunk prints, its exit status, the Exchange folder, the tables read
with `psql` and `received.jsonl`, and nothing else. This module holds the comparisons and the readers of files; the
scenario's home (home.py) holds the readers that need its paths and its server."""

from __future__ import annotations

import json
import time
from collections.abc import Callable
from pathlib import Path
from typing import Any


class Mismatch(AssertionError):
    """A scenario's check that failed, with what it expected and what it found."""

    def __init__(self, message: str, expected: Any = None, actual: Any = None) -> None:
        super().__init__(message)
        self.expected = expected
        self.actual = actual


def check(condition: object, message: str, expected: Any = None, actual: Any = None) -> None:
    if not condition:
        raise Mismatch(message, expected, actual)


def equal(actual: Any, expected: Any, what: str) -> None:
    """Equal as JSON values: `true` is not `1`, and an absent field is not `null`."""
    if json.dumps(actual, sort_keys=True) != json.dumps(expected, sort_keys=True):
        raise Mismatch(f"{what} differs.", expected, actual)


def wait_until[T](probe: Callable[[], T | None], seconds: float, what: str, *, every: float = 0.05) -> T:
    """The first value of `probe` that is not None, False or empty, asked every `every` seconds for `seconds`."""
    deadline = time.monotonic() + seconds
    while True:
        value = probe()
        if value:
            return value
        if time.monotonic() >= deadline:
            raise Mismatch(f"Waited {seconds:g} s for {what}.")
        time.sleep(every)


def json_lines(path: Path) -> list[Any]:
    """The whole lines of a file of JSON lines. A last line without a newline is unfinished and skipped, as every
    reader of `events.jsonl` skips it (RCT-1.9); a line that is not JSON is given as its text."""
    try:
        data = path.read_bytes()
    except FileNotFoundError:
        return []
    lines = data.split(b"\n")[:-1]
    values: list[Any] = []
    for raw in lines:
        text = raw.decode("utf-8", "surrogateescape")
        try:
            values.append(json.loads(text))
        except ValueError:
            values.append(text)
    return values


def parse_line(line: str | None) -> Any:
    """A line the Trunk printed, as JSON, or None when it is none or not JSON."""
    if line is None:
        return None
    try:
        return json.loads(line)
    except ValueError:
        return None


def describe(value: Any, limit: int = 2048) -> str:
    text = json.dumps(value, ensure_ascii=False, sort_keys=True, default=str).encode(
        "utf-8", "backslashreplace").decode("utf-8")
    return text if len(text) <= limit else text[:limit] + "…"
