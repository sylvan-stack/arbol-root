"""Remove only committed or verified abandoned UUID dot directories."""

from __future__ import annotations

import os
import shutil
import stat
import subprocess
import sys
import time

from arbol_root.input import UUID
from arbol_root.listing import project, read_record
from arbol_root.model import Identity, Refusal


def cleanup(context: Identity, *, now: float | None = None) -> bool:
    place = context.folder / 'exchanges'
    try:
        catalogue = os.open(place, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
    except FileNotFoundError:
        return True
    except OSError as error:
        raise Refusal('root_unavailable', f'Cannot enumerate {place}: {error}') from error
    success = True
    clock = time.time() if now is None else now
    try:
        try:
            names = sorted(os.listdir(catalogue))
        except OSError as error:
            raise Refusal('root_unavailable', f'Cannot enumerate {place}: {error}') from error
        for name in names:
            if not name.startswith('.') or name[-4:] not in {'.old', '.new'} or not UUID.fullmatch(name[1:-4]):
                continue
            try:
                original = os.stat(name, dir_fd=catalogue, follow_symlinks=False)
                if not stat.S_ISDIR(original.st_mode):
                    continue
                if name.endswith('.new'):
                    if clock-original.st_mtime <= 15:
                        continue
                    try:
                        record = read_record(catalogue, name)
                    except FileNotFoundError:
                        record = None
                    if record is not None and project(record, context, name[1:-4])['process']['alive']:
                        continue
                current = os.stat(name, dir_fd=catalogue, follow_symlinks=False)
                if (current.st_dev, current.st_ino) != (original.st_dev, original.st_ino):
                    raise ValueError('The dot folder changed while its ownership was checked.')
                if not shutil.rmtree.avoids_symlink_attacks:
                    raise ValueError('This platform cannot remove a dot folder without following replacements.')
                shutil.rmtree(name, dir_fd=catalogue)
            except FileNotFoundError:
                continue
            except (OSError, ValueError, KeyError, TypeError, subprocess.SubprocessError) as error:
                print(f'Kept dot folder {place / name}: {error}', file=sys.stderr)
                success = False
    finally:
        os.close(catalogue)
    return success
