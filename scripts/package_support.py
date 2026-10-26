"""Standalone-runtime metadata and image integrity, owned by the Root manager."""

from __future__ import annotations

import hashlib
import json
import os
import platform
import subprocess
import sys
import tomllib
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from arbol_root.model import BUILD_ID, build_record, identifier, object_file  # noqa: E402

MUTABLE = {"build.json", "build.log", "last-start", "package-manifest.json"}


def digest(path: Path) -> str:
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def files(folder: Path) -> dict[str, str]:
    return {str(path.relative_to(folder)): digest(path) for path in sorted(folder.rglob('*'))
            if path.is_file() and str(path.relative_to(folder)) not in MUTABLE and path.suffix != '.pyc'
            and '__pycache__' not in path.parts}


def metadata(root: Path) -> tuple[str, dict[str, Any]]:
    project = tomllib.loads((root / 'pyproject.toml').read_text())['project']
    version = object_file(root / 'package.json').get('version')
    pin = object_file(root / 'scripts/python-distribution.json')
    if (not isinstance(version, str) or project.get('version') != version or project.get('name') != 'arbol-root'
            or project.get('dependencies') != [] or project.get('requires-python') != '=='+str(pin.get('version'))
            or (root / '.python-version').read_text().strip() != pin.get('version')):
        raise ValueError('The standard-library project, package and Python pin must agree.')
    return version, pin


def target() -> str:
    architecture = {'arm64':'aarch64', 'aarch64':'aarch64', 'x86_64':'x86_64'}.get(platform.machine())
    if sys.platform != 'darwin' or architecture is None:
        raise ValueError('The pinned interpreter supports macOS arm64 and x86_64.')
    return architecture+'-apple-darwin'


def provenance(root: Path) -> dict[str, Any]:
    def git(*args: str) -> str | None:
        p = subprocess.run(['git', *args], cwd=root, capture_output=True, text=True, timeout=15, check=False)
        return p.stdout.strip() if p.returncode == 0 else None
    return {'repository':str(root.resolve()), 'commit':git('rev-parse','HEAD'),
            'branch':git('rev-parse','--abbrev-ref','HEAD'), 'uncommittedChanges':bool(git('status','--porcelain'))}


def destination(candidate: str | None, root: Path) -> tuple[Path, str, str | None]:
    value = candidate if candidate is not None else os.environ.get('ARBOL_BUILD_DIR', '')
    if not value or not Path(value).is_absolute():
        raise ValueError('The package needs an absolute Build folder or candidate.')
    folder = Path(value).resolve(strict=True)
    root = root.resolve()
    if folder == root or folder in root.parents or root in folder.parents:
        raise ValueError('The package cannot overlap its source.')
    allowed = set() if candidate is not None else {'build.json', 'build.log'}
    if any(path.name not in allowed for path in folder.iterdir()):
        raise ValueError('The new package folder already holds files.')
    if candidate is not None:
        return folder, '0', None
    record = object_file(folder / 'build.json')
    version, _pin = metadata(root)
    if (record.get('component') != 'arbol-root' or record.get('entry') != 'bin/arbol-root'
            or record.get('packageVersion') != version or not identifier(record.get('root'))
            or not isinstance(record.get('build'), str) or not BUILD_ID.fullmatch(record['build'])
            or os.environ.get('ARBOL_BUILD_NUMBER') != record['build']):
        raise ValueError('The Build identity must agree with its record.')
    return folder, record['build'], record['root']


def write_manifest(folder: Path, layout: dict[str, Any] | None = None) -> None:
    manifest = object_file(folder / 'package-manifest.json')
    if layout is not None:
        manifest['layout'] = layout
    manifest['files'] = files(folder)
    (folder / 'package-manifest.json').write_text(json.dumps(manifest, indent=2)+'\n')


def verify(folder: Path) -> None:
    manifest = object_file(folder / 'package-manifest.json')
    record = build_record(folder)
    if (manifest.get('component') != 'arbol-root' or manifest.get('candidate') is not False
            or manifest.get('build') != record['build'] or manifest.get('root') != record['root']
            or manifest.get('packageVersion') != record['packageVersion']
            or manifest.get('layout', {}).get('root') != record['root']):
        raise ValueError('The packaged identity and copied layout must match the numbered Build.')
    if manifest.get('files') != files(folder):
        raise ValueError('The package file manifest does not match the image.')
    executable = folder / manifest['python']['executable']
    if manifest['python']['executableSha256'] != digest(executable):
        raise ValueError('The packaged interpreter has changed.')
