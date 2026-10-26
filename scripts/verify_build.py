"""Private end-to-end qualification through the installed Build Tool; no owner Root."""

from __future__ import annotations

import argparse
import json
import os
import re
import shlex
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import Any


def qualify(source: Path, tool: Path, cache: Path) -> dict[str, Any]:
    source, tool, cache = source.resolve(), tool.resolve(), cache.resolve()
    specification = source / 'contract/conformance/specifications/03-the-chat-tables.md'
    if not specification.is_file():
        specification = Path.home() / 'Artifacts/arbol-root/contract/03-the-chat-tables.md'
    with tempfile.TemporaryDirectory(prefix='rtm-private-build-') as temporary:
        home = Path(temporary).resolve()
        registry, bin_dir = home / 'registry with spaces', home / '.local/bin'
        env = {'HOME':str(home), 'PATH':os.environ.get('PATH', os.defpath), 'LANG':'en_US.UTF-8',
               'ARBOL_PYTHON_ARCHIVE_CACHE':str(cache)}
        oracle = home / 'Artifacts/arbol-root/contract/03-the-chat-tables.md'
        oracle.parent.mkdir(parents=True)
        shutil.copy2(specification, oracle)
        roots = home / 'Library/Application Support/Arbol/roots'
        for name, state in [('sapling','working'), ('missing','preparing')]:
            folder = roots / name
            folder.mkdir(parents=True)
            (folder / 'root.json').write_text(json.dumps({'root':name, 'rootContract':1, 'status':state,
                                                         'createdAt':'2026-10-26T09:00:00.000Z'}))

        def build(component: str, repo: Path, root: str | None = None, *, succeeds: bool = True) -> dict[str, Any]:
            args = [str(tool),'build',component,'--repo',str(repo),'--registry-dir',str(registry),'--bin-dir',str(bin_dir)]
            if root is not None:
                args += ['--root',root]
            run = subprocess.run(args, env=env, capture_output=True, text=True, check=False, timeout=600)
            value: dict[str, Any] = json.loads(run.stdout)
            expected = 'working' if succeeds else 'failed'
            if run.returncode != (0 if succeeds else 1) or value.get('status') != expected:
                log = registry / component / str(value.get('build','')) / 'build.log'
                detail = log.read_text()[-12000:] if log.is_file() else run.stderr
                raise ValueError(f'{component} expected {expected}: {run.stdout}\n{detail}')
            return value

        # An actual Build Tool-generated Trunk launcher, backed only by a fictional component.
        fixture = home / 'fictional trunk'
        fixture.mkdir()
        (fixture / 'package.json').write_text('{"version":"1.0.0"}')
        (fixture / 'program').write_text('#!/bin/sh\nexit 0\n')
        (fixture / 'arbol-build.json').write_text(json.dumps({
            'component':'arbol-trunk/fixture', 'entry':'program', 'rootContracts':[1],
            'build':['cp program "$ARBOL_BUILD_DIR/program" && chmod +x "$ARBOL_BUILD_DIR/program"'],
            'checks':[{'name':'fixture','kind':'unit','command':'"$ARBOL_BUILD_DIR/program"'}]}))
        for args in [['git','init','-q','-b','main'],['git','add','--','package.json','program','arbol-build.json'],
                     ['git','commit','-qm','Private Root manager inventory fixture']]:
            subprocess.run(args, cwd=fixture, check=True, capture_output=True)
        build('arbol-trunk/fixture', fixture)
        good = build('arbol-root', source, 'sapling')
        folder = registry / 'arbol-root' / good['build']
        for name, original in [('chat-tables.sql','contract/1/layout.sql'), ('root-tables.sql','roots/sapling/layout.sql')]:
            if (folder / 'layout' / name).read_bytes() != (source / original).read_bytes():
                raise ValueError(f'The packaged {name} differs from its source.')
        if (folder / 'layout/migrate.sql').exists():
            raise ValueError('A Root with no lineage must carry no migration.')
        expected = subprocess.run([str(bin_dir / 'arbol-trunk'),'--root','sapling','list'],
                                  env=env, capture_output=True, check=True).stdout
        listed = json.loads(expected)
        if not listed['trunks'][0]['builds'][0]['chosen']:
            raise ValueError('The private compatible Trunk was not chosen.')
        # Discover by name in a new clean login shell, using only this private launchers folder.
        shell_env = {**env, 'PATH':str(bin_dir)+os.pathsep+env['PATH']}
        command = 'export PATH='+shlex.quote(str(bin_dir))+':"$PATH"; command -v arbol-root; arbol-root --root sapling trunks'
        probe = subprocess.run(['/bin/zsh','-l','-i','-c',command], env=shell_env, capture_output=True, check=True)
        found, _newline, answer = probe.stdout.partition(b'\n')
        if Path(found.decode()).resolve() != (bin_dir / 'arbol-root').resolve() or answer != expected:
            raise ValueError(f'The fresh-login Root launcher differs from Trunk inventory: {probe.stdout!r}')
        bad = build('arbol-root', source, 'missing', succeeds=False)
        bad_log = (registry / 'arbol-root' / bad['build'] / 'build.log').read_text()
        if 'Missing regular SQL file' not in bad_log or 'roots/missing/layout.sql' not in bad_log:
            raise ValueError('The missing-layout Build failed for an unexpected reason.')
        unit_log = (folder / 'build.log').read_text()
        if re.search(r'skipped=\d+', unit_log):
            raise ValueError('The private manager Build skipped a required unit check.')
        manifest = json.loads((folder / 'package-manifest.json').read_text())
        # Save evidence outside git; temporary homes, registry and fictional Git repo are removed on return.
        return {'check':'root.private-build', 'working':good['build'], 'failedMissingLayout':bad['build'],
                'checks':good['checks'], 'unitSummaries':re.findall(r'Ran \d+ tests in [\d.]+s', unit_log),
                'noSkippedTests':True, 'python':manifest['python'], 'source':manifest['source'],
                'packagedFiles':{name:digest for name,digest in manifest['files'].items()
                                 if name.startswith(('src/','scripts/','tests/','bin/','contract/','roots/'))},
                'trunks':listed, 'freshLoginName':True, 'replyBytesIdentical':True,
                'ownerRootsChanged':False, 'vendorRequests':0, 'temporaryStateRemovedOnReturn':True}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument('--tool', type=Path, default=Path.home() / '.local/bin/arbol-builds')
    parser.add_argument('--cache', type=Path, default=Path.home() / '.cache/arbol-driver-build/python')
    args = parser.parse_args()
    print(json.dumps(qualify(args.source, args.tool, args.cache), indent=2))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
