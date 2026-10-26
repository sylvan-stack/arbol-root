"""Delegate persistence to one exact compatible Trivial Build, never open its payloads."""

from __future__ import annotations

import json
from typing import Any

from arbol_root.cleanup import cleanup
from arbol_root.launcher import Reply, chosen_build, command_reply
from arbol_root.listing import listing
from arbol_root.model import Identity, Refusal


def failure(exchange: str, error: Refusal) -> dict[str, Any]:
    value: dict[str, Any] = {'exchange':exchange, 'error':{'code':error.code, 'message':str(error)}}
    if error.available is not None:
        value['available'] = error.available
    return value


def settle_one(context: Identity, number: str, exchange: str) -> tuple[dict[str, Any], int]:
    try:
        reply = command_reply(context.root, ['trivial', '-v', number, 'settle', exchange], context.bin_dir, 'settle')
        return {'exchange':exchange, **reply.value}, reply.status
    except Refusal as error:
        return failure(exchange, error), 1


def settle_after_stop(context: Identity, exchange: str) -> dict[str, Any]:
    """A process can be ended even when selection or saving is refused."""
    try:
        number = chosen_build(context, 'trivial')
        if isinstance(number, Reply):
            return {'exchange':exchange, **number.value}
        return settle_one(context, number, exchange)[0]
    except Refusal as error:
        return failure(exchange, error)


def settle(context: Identity, exchange: str | None = None) -> Reply:
    cleaned = cleanup(context) if exchange is None else True
    unreadable: set[str] = set()
    if exchange is not None:
        targets = {exchange}
    else:
        view = listing(context)
        targets = {entry['exchange'] for entry in view['exchanges'] if not entry['process']['alive']}
        unreadable = set(view['unreadable'])
    number: str | Reply | None = chosen_build(context, 'trivial') if targets else None
    if isinstance(number, Reply):
        return number
    results: list[dict[str, Any]] = []
    status = 0 if cleaned else 1
    for name in sorted(targets | unreadable):
        if name in unreadable:
            value, failed = failure(name, Refusal('root_unavailable', 'Cannot verify this Exchange record/process.')), 1
        else:
            assert number is not None
            value, failed = settle_one(context, number, name)
        results.append(value)
        status = max(status, failed)
        if isinstance(value.get('error'), dict) and value['error'].get('code') == 'database_unavailable':
            break
    document = {'root':context.root, 'results':results}
    return Reply((json.dumps(document, ensure_ascii=True)+'\n').encode(), document, status)
