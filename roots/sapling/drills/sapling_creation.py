"""Create First Sapling once; never replay destructive steps over an existing Root."""

from __future__ import annotations

import os
import subprocess
import uuid
from collections.abc import Callable
from pathlib import Path
from typing import Any

from drill_support import Commands, Inspector, Places, new_json, require


def merged_source(source: Path) -> str:
    def git(*args: str) -> str:
        return subprocess.check_output(['git','-C',str(source),*args],text=True,timeout=15).strip()
    require(git('branch','--show-current') == 'main', 'The manager Build source must be merged main.')
    require(not git('status','--porcelain'), 'The merged manager Build source must be clean.')
    require(source.resolve() == (Path.home()/'repos/sylvan-stack/readonly/arbol-root').resolve(),
            'The actual manager Build must read readonly/arbol-root.')
    return git('rev-parse','HEAD')


def make_sapling(places: Places, source: Path, *, commands: Commands | None = None,
                 inspector: Callable[[Places], Inspector] = Inspector) -> dict[str, Any]:
    calls = commands or Commands(places)
    retained = calls.run('arbol-roots','list')
    require(isinstance(retained,list), 'The Root catalogue did not return a list.')
    require(not any(row.get('root') == 'sapling' for row in retained),
            'First Sapling already exists; inspect it and its receipt instead of recreating it.')
    require(not os.path.lexists(places.roots/'sapling')
            and not os.path.lexists(places.home/'.arbol/roots/sapling'),
            'First Sapling has existing state/settings; no create, migrate or removal was attempted.')
    commit = merged_source(source)
    receipt = places.evidence/'creation-attempts'/str(uuid.uuid4())
    new_json(receipt/'planned.json',{'root':'sapling','name':'First Sapling','source':str(source),'commit':commit})
    phase = 'create'
    try:
        created = calls.run('arbol-roots','create','sapling','--name','First Sapling',seconds=45)
        require(created.get('root') == 'sapling' and created.get('name') == 'First Sapling'
                and created.get('status') == 'preparing' and created.get('rootContract') == 1
                and 'grewFrom' not in created, 'Unexpected First Sapling creation record; inspect the receipt.')
        new_json(receipt/'created.json',created)
        phase = 'build'
        built = calls.run('arbol-builds','build','arbol-root','--root','sapling','--repo',str(source),seconds=1200)
        require(built.get('root') == 'sapling' and built.get('status') == 'working'
                and built.get('checks') == [{'name':name,'passed':True} for name in ['unit','layout','migration']],
                'The actual manager Build did not pass all three checks.')
        require(built.get('source',{}).get('commit') == commit
                and built.get('source',{}).get('branch') == 'main'
                and built.get('source',{}).get('uncommittedChanges') is False,
                'The manager Build does not identify the expected clean merged source.')
        new_json(receipt/'build.json',built)
        number = built['build']
        phase = 'migrate'
        migrated = calls.run('arbol-roots','migrate','sapling',seconds=180)
        require(migrated.get('root') == 'sapling' and migrated.get('rootBuild') == number,
                'Migrate did not use the manager Build just qualified.')
        new_json(receipt/'migrated.json',migrated)
        phase = 'ready'
        ready = calls.run('arbol-roots','ready','sapling')
        require(ready.get('root') == 'sapling' and ready.get('status') == 'working', 'First Sapling was not marked working.')
        new_json(receipt/'ready.json',ready)
        phase = 'inspect'
        counts = inspector(places).counts()
        require(set(counts) == {'chats','exchanges','messages','tool_calls','runs'} and not any(counts.values()),
                'The five initial chat tables must exist and be empty.')
        listed = calls.run('arbol-roots','list')
        require(any(row.get('root') == 'sapling' and row.get('current') is True for row in listed),
                'First Sapling is not the current Root.')
        manager = calls.run('arbol-root','--root','sapling','list')
        require(manager.get('root') == 'sapling' and manager.get('rootBuild') == number
                and manager.get('exchanges') == [] and manager.get('unreadable') == [],
                'The installed manager did not report the new Root/Build and empty Exchange catalogue.')
        result = {'passed':True,'check':'sapling.create','root':'sapling','rootBuild':number,'sourceCommit':commit,
                  'tables':counts,'current':True,'receipt':str(receipt),'vendorRequests':0}
        new_json(receipt/'qualified.json',result)
        return result
    except BaseException as error:
        new_json(receipt/'failure.json',{'phase':phase,'error':str(error),'root':'sapling',
                                        'next':'Inspect this receipt and the Root; never automatically recreate it.'})
        raise
