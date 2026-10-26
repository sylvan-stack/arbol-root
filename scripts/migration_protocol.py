"""The prescribed private two-database copy protocol, without running SQL."""

from __future__ import annotations

import re

from scripts.sql_statements import Statement, statements

COPY = re.compile(r"\\copy\s+.+\s+(TO|FROM)\s+'([A-Za-z][A-Za-z_0-9]*\.copy)'\s+WITH\s+\(FORMAT\s+binary\)", re.I)
REQUIRED = {'chats.copy','exchanges.copy','messages.copy','tool_calls.copy','runs.copy'}
SOURCE = [('begin','isolation','level','repeatable','read','read','only'),
          ('select','now','(',')','as','snapshot'), ('commit',)]


def protocol(source: str) -> set[str]:
    phase = 0
    active = {1:False,2:False}
    sql: dict[int,list[Statement]] = {1:[],2:[]}
    copied: dict[int,set[str]] = {1:set(),2:set()}
    buffer: list[str] = []
    named = False
    snapshot = False

    def flush() -> None:
        for statement in statements('\n'.join(buffer)):
            if phase == 0:
                raise ValueError('Migration SQL must run only on its two private connections.')
            if statement[0] == 'begin':
                if active[phase]:
                    raise ValueError('A migration phase has more than one transaction.')
                active[phase] = True
            elif statement == ('commit',):
                if not active[phase]:
                    raise ValueError('Migration COMMIT is outside its transaction.')
                active[phase] = False
            elif not active[phase]:
                raise ValueError('A migration statement is outside its transaction.')
            sql[phase].append(statement)
        buffer.clear()

    for line in source.splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith('--'):
            continue
        if stripped.startswith('\\'):
            flush()
            if re.fullmatch(r'\\set\s+to_database\s+:DBNAME',stripped):
                if phase or named:
                    raise ValueError('to_database is set once from the initial private DBNAME.')
                named = True
                continue
            if re.fullmatch(r'\\connect\s+:from_database',stripped):
                if phase != 0 or not named:
                    raise ValueError('The source connection must be first and use from_database.')
                phase = 1
                continue
            if re.fullmatch(r'\\connect\s+:to_database',stripped):
                if phase != 1 or active[1]:
                    raise ValueError('The destination connection follows the committed source snapshot.')
                phase = 2
                continue
            match = COPY.fullmatch(stripped)
            if match:
                direction, filename = match.groups()
                expected = 1 if direction.upper() == 'TO' else 2
                if phase != expected or not active[phase] or filename in copied[phase]:
                    raise ValueError('A binary copy must run once inside its corresponding transaction.')
                copied[phase].add(filename)
                continue
            raise ValueError('Migration metadata must use only its two database variables and bare binary copy files.')
        if '\\gset' in stripped:
            if phase != 1 or snapshot or not re.fullmatch(r'SELECT\s+now\(\)\s+AS\s+snapshot\s+\\gset',stripped,re.I):
                raise ValueError('Only the source snapshot time may be captured by gset.')
            snapshot = True
            buffer.append(stripped.replace('\\gset',';'))
            flush()
        else:
            buffer.append(line)
    flush()
    if phase != 2 or any(active.values()) or sql[1] != SOURCE or not snapshot:
        raise ValueError('Migration needs one REPEATABLE READ READ ONLY source snapshot and a committed destination.')
    target = sql[2]
    if (not target or target[0] != ('begin',) or target[-1] != ('commit',)
            or sum(statement[0] == 'begin' for statement in target) != 1
            or sum(statement == ('commit',) for statement in target) != 1):
        raise ValueError('The destination writes must be in exactly one transaction.')
    if copied[1] != copied[2] or not REQUIRED <= copied[1]:
        raise ValueError('Every required table is copied once out of the source and once into the destination.')
    return copied[1]
