"""Fictional chats for RTM-1; no account, process, Root or server outside a check."""

from __future__ import annotations

import json
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from rct_conformance.postgres import Server

CHATS = ['10000000-0000-4000-8000-000000000001', '10000000-0000-4000-8000-000000000002']
EXCHANGES = [f'20000000-0000-4000-8000-{i:012d}' for i in range(1, 5)]
SPECIAL = '🌲 �\r\n\tC:\\fixture\\path  '


def text(value: str) -> str:
    return "convert_from(decode('"+value.encode('utf-8').hex()+"','hex'),'UTF8')"


def document(value: Any) -> str:
    return text(json.dumps(value, ensure_ascii=False))+'::jsonb'


def seed(server: Server, database: str) -> None:
    statements: list[str] = []
    for i, chat in enumerate(CHATS, 1):
        statements.append(f"INSERT INTO chats VALUES ('{chat}',{text('Fictional '+str(i)+' 🌲')},'2026-10-15T09:00:00Z');")
    failure = {'code':'fictional_failure','message':SPECIAL,'retryable':False,'extra':{'preserved':True}}
    for i, (exchange, state) in enumerate(zip(EXCHANGES, ['completed','failed','open','cancelled'], strict=True)):
        chat, number = (CHATS[0],i+1) if i < 3 else (CHATS[1],1)
        ended = 'NULL' if state == 'open' else "'2026-10-15T09:01:00Z'"
        error = document(failure) if state == 'failed' else 'NULL'
        route = document({'driver':'fictional','subscription':'fictional','model':'fictional'})
        statements.append('INSERT INTO exchanges '
                          '(id,chat_id,number,state,error,trunk,build,route,working_folder,accepted_at,ended_at) '
                          f"VALUES ('{exchange}','{chat}',{number},'{state}',{error},'trivial','a',{route},"
                          f"'/fictional/work','2026-10-15T09:00:00Z',{ended});")
        if i != 1:
            for position, role in [(0,'user'),(1,'assistant')]:
                statements.append(f"INSERT INTO messages VALUES ('{exchange}',{position},'{role}',{text(role+' '+SPECIAL)});")
            statements.append('INSERT INTO tool_calls '
                              '(exchange_id,position,run_id,call_id,name,input,ok,result,interrupted) '
                              f"VALUES ('{exchange}',2,'fictional-run','call-1','Read',"
                              f"{document({'path':SPECIAL,'nested':{'kept':[1,True,None]}})},false,"
                              f"{document({'output':SPECIAL,'extra':[1,2]})},true);")
        usage = document({'inputTokens':12,'outputTokens':3,'costUSD':0.00001,'extra':{'kept':True}})
        outcome = 'failed' if i == 1 else 'cancelled' if i == 3 else 'completed'
        cause = document(failure) if outcome == 'failed' else 'NULL'
        statements.append('INSERT INTO runs (exchange_id,run_id,outcome,usage,error,started,ended_at) '
                          f"VALUES ('{exchange}','fictional-run','{outcome}',{usage},{cause},"
                          f"{document({'model':'fictional','extra':SPECIAL})},'2026-10-15T09:01:00Z');")
    statements.append(f"UPDATE exchanges SET replaced_by='{EXCHANGES[2]}' WHERE id='{EXCHANGES[1]}';")
    server.execute(database, '\n'.join(statements))
