"""Two explicitly approved Haiku messages, with no automatic submission retry."""

from __future__ import annotations

import math
import time
import uuid
from decimal import Decimal
from typing import Any

from drill_support import Budget, Commands, Inspector, Places, new_json, require, wait_for


def snapshot(inspector: Inspector, exchange: str) -> dict[str, Any]:
    require(str(uuid.UUID(exchange)) == exchange, 'A message inspection needs its canonical Exchange UUID.')
    where = " WHERE exchange_id='"+exchange+"'"
    result = inspector.read("SELECT json_build_object('exchange',"
        "(SELECT row_to_json(e) FROM exchanges e WHERE id='"+exchange+"'),'messages',"
        "(SELECT coalesce(json_agg(m ORDER BY position),'[]') FROM messages m"+where+"),'runs',"
        "(SELECT coalesce(json_agg(r ORDER BY run_id),'[]') FROM runs r"+where+'))')
    require(isinstance(result,dict), 'The message snapshot is not an object.')
    return dict(result)


def judge(data: dict[str, Any], accepted: dict[str, Any], message: str, number: int,
          *, remembered: str | None = None) -> dict[str, Any]:
    row = data.get('exchange')
    require(isinstance(row,dict) and row.get('id') == accepted['exchange']
            and row.get('chat_id') == accepted['chat'] and row.get('number') == number
            and row.get('state') == 'completed' and row.get('trunk') == 'trivial'
            and row.get('build') == accepted['build'], 'The persisted Exchange identity/state differs.')
    assert isinstance(row,dict)
    require(row.get('route',{}).get('driver') == 'claude'
            and row.get('route',{}).get('subscription') == 'anthropic'
            and row.get('route',{}).get('model') == 'haiku', 'The persisted route is not the approved Haiku route.')
    messages = data.get('messages',[])
    users = [item for item in messages if item.get('role') == 'user']
    answers = [item for item in messages if item.get('role') == 'assistant']
    require(len(users) == 1 and users[0].get('position') == 0 and users[0].get('text') == message
            and answers and all(item.get('text') for item in answers), 'The user message or whole answer is missing.')
    if remembered is not None:
        require(remembered in ''.join(item['text'] for item in answers), 'The second answer did not remember the first word.')
    runs = data.get('runs',[])
    require(runs and all(item.get('outcome') == 'completed' and isinstance(item.get('usage'),dict) for item in runs),
            'The completed Driver run and its token usage are missing.')
    tokens = {name:sum(item['usage'].get(name,0) for item in runs) for name in ['inputTokens','outputTokens']}
    require(tokens['inputTokens'] > 0 and tokens['outputTokens'] > 0, 'The real answer has no reported input/output tokens.')
    costs = [item['usage'].get('costUSD') for item in runs]
    cost = str(sum((Decimal(str(value)) for value in costs),Decimal(0))) if all(value is not None for value in costs) else None
    return {'exchange':accepted['exchange'],'chat':accepted['chat'],'number':number,'trunkBuild':accepted['build'],
            **tokens,'reportedCostUSD':cost,'remembered':remembered is not None,'runs':runs}


def real_messages(places: Places, *, send: bool = False, commands: Commands | None = None,
                  inspector: Inspector | None = None) -> dict[str, Any]:
    calls = commands or Commands(places)
    root = calls.run('arbol-roots','show','sapling')
    require(root.get('root') == 'sapling' and root.get('status') == 'working', 'First Sapling must already be working.')
    subscription = calls.run('arbol-claude-driver','subscriptions','check','anthropic')
    require(subscription.get('state') == 'signed_in', 'The normal owner anthropic Subscription is not signed in.')
    usage = calls.run('arbol-claude-driver','subscriptions','usage','anthropic')
    require(usage.get('outcome') == 'ok' and isinstance(usage.get('windows'),list)
            and all(window.get('limitReached') is not True and window.get('usedPercent',0) < 100
                    for window in usage['windows']),
            'The owner usage report is unavailable or reports a reached limit; no message was sent.')
    listing = calls.run('arbol-root','--root','sapling','list')
    require(listing.get('exchanges') == [] and listing.get('unreadable') == [],
            'First Sapling must have no in-progress or unreadable Exchange before the two-message check.')
    budget = Budget(places.evidence)
    history = budget.status()
    require(all((attempt.get('usage') or {}).get('retryNotBeforeUnix',0) <= time.time()
                for attempt in history['attempts']),
            'The last vendor rate-limit deadline has not passed; no fresh message was sent.')
    remaining = history['remaining']
    require(remaining >= 2, 'Two messages do not fit in the remaining owner allowance; none was sent.')
    if not send:
        return {'check':'sapling.real-messages','preflightOnly':True,'plannedSubmissions':2,'remaining':remaining,
                'route':{'driver':'claude','subscription':'anthropic','model':'haiku'}}
    database = inspector or Inspector(places)
    folder = places.evidence/'message-attempts'/str(uuid.uuid4())
    work = folder/'work'
    work.mkdir(parents=True,mode=0o700)
    word = 'pine'+uuid.uuid4().hex[:16]
    prompts = [f'Remember this exact verification word for this chat: {word}. Reply with only the word remembered.',
               'What exact verification word did I give you in my previous message? Reply with that word only.']
    chat: str | None = None
    results = []
    for number, message in enumerate(prompts,1):
        exchange = str(uuid.uuid4())
        budget.reserve(exchange)
        started = False
        data: dict[str, Any] | None = None
        try:
            request = folder/(exchange+'-request.json')
            value = {'message':message,'route':{'driver':'claude','subscription':'anthropic','model':'haiku'},
                     'workingFolder':str(work)}
            new_json(request,value)
            new_json(folder/(exchange+'-submission.json'),{'exchange':exchange,'chat':chat,'number':number,**value})
            args = ['--root','sapling','start','trivial','--exchange',exchange,'--request',str(request)]
            if chat is not None:
                args += ['--chat',chat]
            began = time.monotonic()
            started = True
            accepted = calls.run('arbol-root',*args,seconds=25,cwd=work)
            elapsed = time.monotonic()-began
            require(elapsed < 20 and accepted.get('accepted') is True and accepted.get('duplicate') is False
                    and accepted.get('root') == 'sapling' and accepted.get('exchange') == exchange
                    and accepted.get('trunk') == 'trivial' and accepted.get('number') == number,
                    'The bounded new acceptance did not identify First Sapling/Trivial/the intended Exchange.')
            require(chat is None or accepted.get('chat') == chat, 'The second message changed chats.')
            chat = str(uuid.UUID(accepted['chat']))
            new_json(folder/(exchange+'-accepted.json'),{'elapsedSeconds':elapsed,**accepted})
            running = calls.run('arbol-root','--root','sapling','list')
            require(any(row.get('exchange') == exchange and row.get('state') == 'running'
                        for row in running.get('exchanges',[])), 'The manager did not show the accepted Exchange running.')
            new_json(folder/(exchange+'-running.json'),running)

            def finished(selected: str = exchange) -> dict[str, Any] | None:
                data = snapshot(database,selected)
                row = data.get('exchange')
                if (isinstance(row,dict) and row.get('state') in ('completed','failed','cancelled','interrupted')
                        and not (places.roots/'sapling/exchanges'/selected).exists()):
                    return data
                return None

            data = wait_for(finished,seconds=300,interval=0.2)
            new_json(folder/(exchange+'-persisted.json'),data)
            verdict = judge(data,accepted,message,number,remembered=word if number == 2 else None)
            new_json(folder/(exchange+'-verdict.json'),verdict)
            budget.finish(exchange,'completed',usage={key:verdict[key] for key in
                                                    ['inputTokens','outputTokens','reportedCostUSD']})
            results.append(verdict)
        except BaseException as error:
            recorded: dict[str, Any] | None = None
            failure = (data or {}).get('exchange') or {}
            refusal = failure.get('error') or {}
            retry = refusal.get('retryAfterSeconds')
            if (refusal.get('code') == 'rate_limited' and isinstance(retry,(float,int))
                    and not isinstance(retry,bool) and math.isfinite(retry) and retry >= 0):
                recorded = {'outcome':'failed','error':'rate_limited','retryNotBeforeUnix':time.time()+retry}
            budget.finish(exchange,'ambiguous' if started else 'no_vendor',usage=recorded)
            new_json(folder/(exchange+'-failure.json'),{'error':str(error),'started':started,
                                                      'next':'Inspect this attempt; do not automatically submit it again.'})
            # Only this attempt's own Exchange can be asked to stop; never another chat/run.
            if started and (places.roots/'sapling/exchanges'/exchange).exists():
                try:
                    calls.run('arbol-root','--root','sapling','stop',exchange,seconds=40)
                except Exception:
                    pass
            raise
    total = (str(sum((Decimal(row['reportedCostUSD']) for row in results),Decimal(0)))
             if all(row['reportedCostUSD'] is not None for row in results) else None)
    report = {'check':'sapling.real-messages','passed':True,'root':'sapling','chat':chat,'messages':results,
              'reportedCostUSD':total,'submissions':2,'budget':budget.status(),'evidence':str(folder),
              'tables':database.counts()}
    new_json(folder/'qualified.json',report)
    return report
