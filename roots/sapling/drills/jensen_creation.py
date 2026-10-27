"""Create the owner-named second Root once and qualify only merged manager source."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import signal
import uuid
from pathlib import Path
from types import FrameType
from typing import Any

from drill_support import Commands, Inspector, Places, new_json, require
from migration_support import Snapshot, fingerprints
from sapling_creation import merged_source


def settings(folder: Path) -> dict[str, Any]:
    require(folder.is_dir() and not folder.is_symlink(), 'The source settings folder must be a real directory.')
    result = {}
    for item in sorted(folder.rglob('*')):
        require(not item.is_symlink() and (item.is_file() or item.is_dir()), 'Unsafe settings entry; creation refuses.')
        result[str(item.relative_to(folder))] = {'kind':'file' if item.is_file() else 'directory',
            'sha256':hashlib.sha256(item.read_bytes()).hexdigest() if item.is_file() else None}
    return result


def make_jensen(places: Places, source: Path, *, commands: Commands | None = None) -> dict[str, Any]:
    calls = commands or Commands(places)
    retained = calls.run('arbol-roots','list')
    require(any(x.get('root') == 'sapling' and x.get('status') == 'working' and x.get('current') for x in retained),
            'First Sapling must remain working/current before Jensen creation.')
    require(not any(x.get('root') == 'jensen' for x in retained)
            and not os.path.lexists(places.roots/'jensen')
            and not os.path.lexists(places.home/'.arbol/roots/jensen'),
            'Jensen has existing state/settings; inspect its receipt instead of recreating it.')
    for row in retained:
        listing = calls.run('arbol-root','--root',row['root'],'list')
        require(listing.get('exchanges') == [] and listing.get('unreadable') == [],
                'Unrelated or unreadable Exchange work prevents creation qualification.')
    require(not list((places.driver/'runs').iterdir()), 'A normal Claude run prevents creation qualification.')
    commit = merged_source(source)
    before = Snapshot(Inspector(places)).read()
    source_record = (places.roots/'sapling/root.json').read_bytes()
    copied_settings = settings(places.home/'.arbol/roots/sapling')
    attempt = places.evidence/'second-root-attempts'/str(uuid.uuid4())
    new_json(attempt/'planned.json',{'root':'jensen','name':'Jensen Root','grewFrom':'sapling',
                                   'sourceCommit':commit,'source':str(source),'sourceFingerprint':fingerprints(before)})
    phase = 'create'
    try:
        created = calls.run('arbol-roots','create','jensen','--name','Jensen Root','--from','sapling',seconds=45)
        new_json(attempt/'created.json',created)
        require(created.get('root') == 'jensen' and created.get('name') == 'Jensen Root'
                and created.get('status') == 'preparing' and created.get('grewFrom') == 'sapling'
                and created.get('rootContract') == 1, 'The created Jensen identity/lineage/state differs.')
        require(settings(places.home/'.arbol/roots/jensen') == copied_settings,
                'Jensen did not copy First Sapling settings exactly.')
        target = Inspector(places,root='jensen')
        tables = "SELECT coalesce(json_agg(tablename ORDER BY tablename),'[]') FROM pg_tables WHERE schemaname='public'"
        require(target.read(tables) == [], 'The new Jensen database is not empty.')
        phase = 'build'
        built = calls.run('arbol-builds','build','arbol-root','--root','jensen','--repo',str(source),seconds=1200)
        new_json(attempt/'build.json',built)
        checks = [{'name':name,'passed':True} for name in ['unit','layout','migration']]
        require(built.get('status') == 'working' and built.get('root') == 'jensen' and built.get('checks') == checks,
                'Jensen manager did not pass all three actual packaged checks; inspect the Build/log.')
        require(built.get('source',{}).get('commit') == commit and built['source'].get('branch') == 'main'
                and built['source'].get('uncommittedChanges') is False, 'Jensen manager did not use merged clean source.')
        number = built['build']
        folder = places.home/'Library/Application Support/Arbol/builds/arbol-root'/number
        for name,original in [('chat-tables.sql','contract/1/layout.sql'),
                              ('root-tables.sql','roots/jensen/layout.sql'),('migrate.sql','roots/jensen/migrate.sql')]:
            require((folder/'layout'/name).read_bytes() == (source/original).read_bytes(),
                    'The installed Jensen layout/migration differs from its merged source.')
        require(target.read(tables) == [], 'A Build check changed the owner Jensen database.')
        require(calls.run('arbol-roots','show','jensen') == created, 'Building the manager changed Jensen root.json.')
        after = calls.run('arbol-roots','list')
        require([x for x in after if x['root'] != 'jensen'] == retained,
                'Jensen creation/Build changed a pre-existing Root/current selection.')
        require((places.roots/'sapling/root.json').read_bytes() == source_record
                and fingerprints(Snapshot(Inspector(places)).read()) == fingerprints(before),
                'Jensen creation/Build changed First Sapling records or rows.')
        report = {'check':'sapling.second-root-created','passed':True,'root':'jensen','name':'Jensen Root',
                  'rootBuild':number,'built':built,'sourceCommit':commit,'status':'preparing','currentRoot':'sapling',
                  'settingsCopied':True,'ownerDatabaseEmpty':True,'sourceUnchanged':True,
                  'evidence':str(attempt),'realMessages':0}
        new_json(attempt/'qualified.json',report)
        return report
    except BaseException as error:
        new_json(attempt/'failure.json',{'phase':phase,'error':str(error),
                                       'next':'Inspect retained Root/Build/receipt before an explicit recovery; never recreate.'})
        raise


def entry() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--run',action='store_true')
    args = parser.parse_args()
    previous = {n:signal.getsignal(n) for n in (signal.SIGINT,signal.SIGTERM)}
    def interrupted(number: int, frame: FrameType | None) -> None:
        raise KeyboardInterrupt('Jensen creation interrupted by signal '+str(number))
    try:
        for number in previous:
            signal.signal(number,interrupted)
        if args.run:
            places = Places.owner()
            report = make_jensen(places,places.home/'repos/sylvan-stack/readonly/arbol-root')
        else:
            report = {'preflightOnly':True,'root':'jensen','name':'Jensen Root','realMessages':0,'planned':'create and build'}
        print(json.dumps(report))
        return 0
    except (Exception,KeyboardInterrupt) as error:
        print(json.dumps({'passed':False,'error':str(error)}))
        return 1
    finally:
        for number,handler in previous.items():
            signal.signal(number,handler)
