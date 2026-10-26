"""Complete SQL statements, preserving quoted values while ignoring presentation."""

import re

QUOTED = re.compile(
    r"""[Ee]'(?:''|\\.|[^'\\])*'|'(?:''|[^'])*'|"(?:""|[^"])*"|\$(?P<tag>[A-Za-z_][A-Za-z_0-9]*|)\$.*?\$(?P=tag)\$""",
    re.S)
WORD = re.compile(r'[A-Za-z_][A-Za-z_0-9$]*')
type Statement = tuple[str, ...]


def statements(source: str) -> list[Statement]:
    found: list[Statement] = []
    current: list[str] = []
    index = 0
    while index < len(source):
        if source[index].isspace():
            index += 1
            continue
        if source.startswith('--', index):
            end = source.find('\n', index)
            index = len(source) if end < 0 else end+1
            continue
        if source.startswith('/*', index):
            index += 2
            depth = 1
            while depth:
                if index >= len(source):
                    raise ValueError('Unterminated SQL comment.')
                if source.startswith('/*', index):
                    depth += 1
                    index += 2
                elif source.startswith('*/', index):
                    depth -= 1
                    index += 2
                else:
                    index += 1
            continue
        quoted = QUOTED.match(source, index)
        if quoted:
            token = quoted.group()
            current.append('e'+token[1:] if token.startswith(("E'", "e'")) else token)
            index = quoted.end()
            continue
        if source[index] in {'"', "'"} or source[index] == '$' and source.find('$', index+1) >= 0:
            raise ValueError('Unterminated quoted SQL value.')
        word = WORD.match(source, index)
        if word:
            current.append(word.group().lower())
            index = word.end()
            continue
        character = source[index]
        index += 1
        if character == ';':
            if current:
                found.append(tuple(current))
                current = []
        elif character == '\\':
            raise ValueError('A layout cannot contain psql metadata commands.')
        else:
            current.append(character)
    if current:
        raise ValueError('A layout statement must end with a semicolon.')
    return found


def layout_statements(source: str) -> list[Statement]:
    found = statements(source)
    for tokens in found:
        create = tokens[:2] in {('create', 'table'), ('create', 'index')}
        create = create or tokens[:3] == ('create', 'unique', 'index')
        comment = tokens[:2] == ('comment', 'on') and tokens[2:3] in {('table',), ('column',), ('index',)}
        addition = tokens[:2] == ('alter', 'table') and ('add', 'column') in tuple(zip(tokens, tokens[1:], strict=False))
        if addition:
            forbidden = {'alter', 'drop', 'rename', 'set', 'reset', 'constraint', 'check', 'unique', 'primary',
                         'foreign', 'references', 'attach', 'detach', 'enable', 'disable', 'owner', 'validate'}
            addition = not any(token in forbidden for token in tokens[2:])
            depth = 0
            for token in tokens:
                if token in {'(', '['}:
                    depth += 1
                elif token in {')', ']'}:
                    depth -= 1
                elif token == ',' and depth == 0:
                    addition = False
        if not (create or comment or addition) or 'select' in tokens:
            raise ValueError('A layout holds only table/index/column/comment DDL, never data-writing statements.')
    return found


def preserves(earlier: str, later: str) -> None:
    remaining = iter(layout_statements(later))
    for statement in layout_statements(earlier):
        if not any(candidate == statement for candidate in remaining):
            raise ValueError('A complete statement of the earlier Build was edited, removed or reordered.')
