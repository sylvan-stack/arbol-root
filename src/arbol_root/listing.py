"""List one Root from records only, without following payloads or settling anything."""

from __future__ import annotations

import json
import os
import re
import stat
import subprocess
from typing import Any, NoReturn

from arbol_root.input import UUID
from arbol_root.model import BUILD_ID, Identity, Refusal
from arbol_root.process import process_alive, timestamp

CODE = re.compile(r'[a-z][a-z0-9]{0,31}\Z', re.ASCII)


def not_json(value: str) -> NoReturn:
    raise ValueError(f'{value} is not a JSON number.')


def read_record(catalogue: int, name: str) -> dict[str, Any]:
    directory = os.open(name, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=catalogue)
    try:
        descriptor = os.open('record.json', os.O_RDONLY | os.O_NONBLOCK | os.O_NOFOLLOW, dir_fd=directory)
        with os.fdopen(descriptor, 'r', encoding='utf-8') as stream:
            if not stat.S_ISREG(os.fstat(stream.fileno()).st_mode):
                raise ValueError('record.json is not a regular file.')
            value = json.load(stream, parse_constant=not_json)
        if not isinstance(value, dict):
            raise ValueError('record.json does not hold an object.')
        return value
    finally:
        os.close(directory)


def project(record: dict[str, Any], context: Identity, name: str) -> dict[str, Any]:
    if (record.get('root') != context.root or record.get('exchange') != name or not UUID.fullmatch(name)
            or type(record.get('rootContract')) is not int or record['rootContract'] < 1
            or not isinstance(record.get('chat'), str) or not UUID.fullmatch(record['chat'])
            or not isinstance(record.get('trunk'), str) or not CODE.fullmatch(record['trunk'])
            or not isinstance(record.get('build'), str)
            or not (record['build'] == '0' or BUILD_ID.fullmatch(record['build']))
            or not isinstance(record.get('process'), dict) or not isinstance(record.get('signsOfLife'), dict)):
        raise ValueError('The record does not supply this Exchange’s listing fields.')
    life = record['signsOfLife']
    if (type(life.get('heartbeat')) is not int or life['heartbeat'] < 0
            or not isinstance(life.get('waitingFor'), str) or not life['waitingFor']):
        raise ValueError('The record has unreadable signs of life.')
    timestamp(life.get('since'))
    if 'acceptedAt' in record:
        timestamp(record['acceptedAt'])
    end = record.get('end')
    if 'end' in record:
        if not isinstance(end, dict) or not isinstance(end.get('state'), str) or not end['state']:
            raise ValueError('The record has an unreadable end.')
        timestamp(end.get('at'))
        if 'error' in end:
            error = end['error']
            if (not isinstance(error, dict) or not isinstance(error.get('code'), str)
                    or not isinstance(error.get('message'), str)):
                raise ValueError('The end has an unreadable error.')
    alive = process_alive(record['process'])
    if 'acceptedAt' not in record:
        state = 'accepting' if alive else 'unaccepted'
    elif 'end' in record:
        state = 'ending' if alive else 'unsaved'
    else:
        state = 'running' if alive else 'interrupted'
    result = {key:record[key] for key in ['root','exchange','chat','trunk','build']}
    result['process'] = {key:record['process'][key] for key in ['pid','startedAt']}
    result['process']['alive'] = alive
    result['state'] = state
    result['signsOfLife'] = {key:life[key] for key in ['heartbeat','waitingFor','since']}
    if end is not None:
        result['end'] = {key:end[key] for key in ['state','at','error'] if key in end}
    return result


def listing(context: Identity) -> dict[str, Any]:
    result: dict[str, Any] = {'root':context.root, 'rootBuild':context.build, 'rootPackageVersion':context.version,
                              'exchanges':[], 'unreadable':[]}
    place = context.folder / 'exchanges'
    try:
        catalogue = os.open(place, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
    except FileNotFoundError:
        return result
    except OSError as error:
        raise Refusal('root_unavailable', f'Cannot enumerate {place}: {error}') from error
    try:
        try:
            with os.scandir(catalogue) as entries:
                names = sorted((entry.name,entry.is_symlink(),entry.is_dir(follow_symlinks=False))
                               for entry in entries if not entry.name.startswith('.'))
        except OSError as error:
            raise Refusal('root_unavailable', f'Cannot enumerate {place}: {error}') from error
        for name, symlink, directory in names:
            if symlink:
                result['unreadable'].append(name)
                continue
            if not directory:
                continue
            try:
                record = read_record(catalogue, name)
                # A Trunk may have renamed/removed the folder after its record was read.
                os.stat(name, dir_fd=catalogue, follow_symlinks=False)
                result['exchanges'].append(project(record, context, name))
            except (OSError, ValueError, KeyError, TypeError, subprocess.SubprocessError):
                try:
                    os.stat(name, dir_fd=catalogue, follow_symlinks=False)
                except FileNotFoundError:
                    continue
                except OSError:
                    pass
                result['unreadable'].append(name)
    finally:
        os.close(catalogue)
    return result
