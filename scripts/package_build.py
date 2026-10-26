"""Package only this manager and its standard-library tests with pinned CPython."""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import tarfile
import tempfile
import urllib.request
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from scripts.package_support import ROOT, destination, digest, files, metadata, provenance, target  # noqa: E402

ARCHIVES = 'https://github.com/astral-sh/python-build-standalone/releases/download/'


def archive(distribution: dict[str, Any]) -> Path:
    checksum, url = distribution.get('sha256'), distribution.get('url')
    if (not isinstance(checksum, str) or not re.fullmatch('[0-9a-f]{64}', checksum)
            or not isinstance(url, str) or not url.startswith(ARCHIVES)):
        raise ValueError('The Python archive needs an official URL and a pinned SHA-256.')
    cache = Path(os.environ.get('ARBOL_PYTHON_ARCHIVE_CACHE', str(Path.home() / '.cache/arbol-driver-build/python')))
    cache.mkdir(parents=True, exist_ok=True)
    saved = cache / (checksum+'.tar.gz')
    if saved.exists():
        if digest(saved) != checksum:
            raise ValueError('The cached Python archive has the wrong SHA-256.')
        return saved
    fd, name = tempfile.mkstemp(prefix='python-', suffix='.tar.gz', dir=cache)
    os.close(fd)
    temporary = Path(name)
    try:
        with urllib.request.urlopen(url, timeout=60) as source, temporary.open('wb') as output:
            shutil.copyfileobj(source, output)
        if digest(temporary) != checksum:
            raise ValueError('The downloaded Python archive has the wrong SHA-256.')
        temporary.replace(saved)
    finally:
        temporary.unlink(missing_ok=True)
    return saved


def package(candidate: str | None = None, *, root: Path = ROOT) -> Path:
    folder, number, selected = destination(candidate, root)
    version, pin = metadata(root)
    architecture = target()
    distribution = pin['distributions'][architecture]
    compressed = archive(distribution)
    runtime = folder / 'runtime'
    runtime.mkdir(mode=0o700)
    with tarfile.open(compressed, 'r:gz') as bundle:
        bundle.extractall(runtime, filter='data')
    interpreter = runtime / 'python/bin/python3.14'
    probe = subprocess.run([str(interpreter), '-I', '-B', '-c', 'import platform; print(platform.python_version())'],
                           check=True, capture_output=True, text=True, cwd=folder)
    if probe.stdout.strip() != pin['version']:
        raise ValueError('The unpacked interpreter has the wrong version.')
    specification = root / 'contract/conformance/specifications/03-the-chat-tables.md'
    if not specification.is_file():
        specification = Path.home() / 'Artifacts/arbol-root/contract/03-the-chat-tables.md'
    if not specification.is_file():
        raise ValueError('The authoritative RCT-3 document is required for the packaged schema check.')
    ignore = shutil.ignore_patterns('__pycache__', '*.pyc', '.DS_Store')
    for name in ['src', 'scripts', 'tests', 'bin', 'contract', 'roots']:
        shutil.copytree(root / name, folder / name, ignore=ignore)
    for name in ['package.json', 'pyproject.toml', '.python-version', 'uv.lock', 'arbol-build.json', 'README.md']:
        shutil.copy2(root / name, folder / name)
    oracle = folder / 'contract/conformance/specifications/03-the-chat-tables.md'
    oracle.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(specification, oracle)
    manifest = {'format':1, 'component':'arbol-root', 'packageVersion':version, 'entry':'bin/arbol-root',
                'build':number, 'root':selected, 'candidate':candidate is not None, 'source':provenance(root),
                'python':{'version':pin['version'], 'target':architecture, 'provider':pin['provider'],
                          'release':pin['release'], 'archiveUrl':distribution['url'], 'archiveSha256':distribution['sha256'],
                          'executable':'runtime/python/bin/python3.14', 'executableSha256':digest(interpreter)},
                'dependencies':{}, 'files':files(folder)}
    (folder / 'package-manifest.json').write_text(json.dumps(manifest, indent=2)+'\n')
    return folder


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--candidate')
    args = parser.parse_args()
    try:
        print(f'Packaged arbol-root in {package(args.candidate)}')
    except (OSError, ValueError, KeyError, subprocess.SubprocessError, tarfile.TarError) as error:
        print(f'Cannot package arbol-root: {error}', file=sys.stderr)
        return 1
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
