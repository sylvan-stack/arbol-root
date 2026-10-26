"""The last build command: copy this Root's SQL, without running any of it."""

from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from arbol_root.model import build_record, identifier, object_file  # noqa: E402


def copy_layout(folder: Path, *, root: Path = ROOT, home: Path | None = None) -> dict[str, Any]:
    record = build_record(folder)
    selected = record["root"]
    source = object_file((home or Path.home()) / "Library/Application Support/Arbol/roots" / selected / "root.json")
    version = source.get("rootContract")
    if source.get("root") != selected or type(version) is not int or version < 1:
        raise ValueError("The Root record must name this Root and a positive integer Root Contract.")
    older = source.get("grewFrom")
    if "grewFrom" in source and (not identifier(older) or older == selected):
        raise ValueError("grewFrom must name a different valid Root.")
    paths = {"chat-tables.sql": root / "contract" / str(version) / "layout.sql",
             "root-tables.sql": root / "roots" / selected / "layout.sql"}
    if older is not None:
        paths["migrate.sql"] = root / "roots" / selected / "migrate.sql"
    # Preflight every required file before writing even the first copy.
    content: dict[str, bytes] = {}
    for name, path in paths.items():
        if not path.is_file():
            raise ValueError(f"Missing regular SQL file: {path}")
        content[name] = path.read_bytes()
    layout = folder / "layout"
    layout.mkdir(exist_ok=True)
    for name, data in content.items():
        (layout / name).write_bytes(data)
    if older is None:
        (layout / "migrate.sql").unlink(missing_ok=True)
    return {"root": selected, "rootContract": version, "grewFrom": older}


def main() -> int:
    try:
        value = os.environ.get("ARBOL_BUILD_DIR", "")
        if not value or not Path(value).is_absolute():
            raise ValueError("ARBOL_BUILD_DIR must name an absolute numbered Build folder.")
        folder = Path(value).resolve(strict=True)
        record = build_record(folder)
        if os.environ.get("ARBOL_BUILD_NUMBER") != record["build"]:
            raise ValueError("ARBOL_BUILD_NUMBER must match the adjacent Build record.")
        layout = copy_layout(folder)
        if (folder / "package-manifest.json").is_file():
            sys.path.insert(0, str(ROOT))
            from scripts.package_support import write_manifest
            write_manifest(folder, layout)
    except (OSError, ValueError, KeyError) as error:
        print(f"Cannot copy this Root's layout: {error}", file=sys.stderr)
        return 1
    print("Copied this Root's SQL files without executing them.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
