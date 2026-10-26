"""Read this program's identity and its selected Root without settings or SQL."""

from __future__ import annotations

import json
import re
import stat
from dataclasses import dataclass
from pathlib import Path
from typing import Any

ROOT_ID = re.compile(r"[a-z0-9]+\Z", re.ASCII)
BUILD_ID = re.compile(r"[1-9a-f][0-9a-f]*\Z", re.ASCII)


class Refusal(Exception):
    def __init__(self, code: str, message: str, available: list[str] | None = None) -> None:
        super().__init__(message)
        self.code = code
        self.available = available


def object_file(path: Path) -> dict[str, Any]:
    if not stat.S_ISREG(path.stat().st_mode):
        raise ValueError(f"{path.name} is not a regular file.")
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"{path.name} must hold an object.")
    return value


def identifier(value: object) -> bool:
    return isinstance(value, str) and ROOT_ID.fullmatch(value) is not None


@dataclass(frozen=True)
class Identity:
    root: str
    build: str
    version: str
    folder: Path
    bin_dir: Path


def build_record(package: Path) -> dict[str, Any]:
    record = object_file(package / "build.json")
    version = object_file(package / "package.json").get("version")
    if (record.get("component") != "arbol-root" or record.get("entry") != "bin/arbol-root"
            or not identifier(record.get("root")) or not isinstance(record.get("build"), str)
            or not BUILD_ID.fullmatch(record["build"]) or not isinstance(version, str)
            or record.get("packageVersion") != version):
        raise ValueError("The Build record must match arbol-root, its Root, number, entry and package version.")
    return record


def identity(package: Path, options: dict[str, str]) -> Identity:
    selected = options.get("--root")
    if selected is not None and not identifier(selected):
        raise Refusal("invalid_input", "The Root identifier must be one lower-case word of letters and digits.")
    if "--root-dir" in options and "--bin-dir" not in options:
        raise Refusal("invalid_input", "--root-dir requires --bin-dir.")
    try:
        if (package / "build.json").exists() or (package / "build.json").is_symlink():
            record = build_record(package)
            if selected is not None and selected != record["root"]:
                raise Refusal("invalid_input", "--root differs from the Build's Root.")
            selected, number, version = record["root"], record["build"], record["packageVersion"]
        else:
            if selected is None:
                raise Refusal("invalid_input", "--root is required outside a Build.")
            number, version = "0", object_file(package / "package.json")["version"]
    except (OSError, ValueError, KeyError) as error:
        raise Refusal("invalid_input", f"Cannot read this program's identity: {error}") from error
    assert selected is not None
    folder = Path(options.get("--root-dir", str(Path.home() / "Library/Application Support/Arbol/roots" / selected)))
    try:
        record = object_file(folder / "root.json")
        if record.get("root") != selected:
            raise ValueError("The Root record names another Root.")
    except (OSError, ValueError) as error:
        raise Refusal("unknown_root", f"Cannot read Root {selected}: {error}") from error
    return Identity(selected, number, version, folder, Path(options.get("--bin-dir", str(Path.home() / ".local/bin"))))
