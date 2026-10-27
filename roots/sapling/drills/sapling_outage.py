"""A bounded database-away refusal, with restoration before the verdict (ARC-D69)."""

from __future__ import annotations

import hashlib
import os
import plistlib
import select
import signal
import subprocess
import time
import uuid
from collections.abc import Callable, Iterator
from contextlib import contextmanager
from pathlib import Path
from types import FrameType
from typing import Any

from drill_support import Budget, Commands, DrillError, Inspector, Places, new_json, require, wait_for


class Interrupted(KeyboardInterrupt):
    pass


@contextmanager
def stopped(*, stop: Callable[[], None], restore: Callable[[], None], healthy: Callable[[], bool],
            receipt: Path) -> Iterator[None]:
    """Restore even after a partial stop, failed body or catchable termination; keep the truthful receipt."""
    require(healthy(), 'The database must be healthy before an outage drill.')
    previous = {number:signal.getsignal(number) for number in (signal.SIGINT,signal.SIGTERM)}
    result: dict[str, Any] = {'restored':False}

    def interrupted(number: int, frame: FrameType | None) -> None:
        raise Interrupted(f'The outage drill received signal {number}.')

    try:
        for number in previous:
            signal.signal(number,interrupted)
        try:
            stop()
            require(not healthy(), 'The database is still reachable after stopping it.')
            yield
        except BaseException as error:
            result['bodyError'] = type(error).__name__
            raise
        finally:
            # A second Ctrl-C must not abort the bounded restoration already in progress.
            for number in previous:
                signal.signal(number,signal.SIG_IGN)
            try:
                restore()
                wait_for(lambda:True if healthy() else None,seconds=30,interval=0.2)
                result['restored'] = True
            except BaseException as error:
                result['restorationError'] = type(error).__name__
                raise DrillError('Database restoration did not pass its health check; inspect the outage receipt.') from error
            finally:
                new_json(receipt,result)
    finally:
        for number, handler in previous.items():
            signal.signal(number,handler)


class Installed:
    """Only the existing, expected per-user service; never edit or reinstall its configuration."""

    def __init__(self, places: Places, inspector: Inspector) -> None:
        self.places, self.inspector = places, inspector
        self.plist = places.home/'Library/LaunchAgents/com.sylvan-stack.arbol.database.plist'
        data = self.plist.read_bytes()
        self.digest = hashlib.sha256(data).hexdigest()
        value = plistlib.loads(data)
        self.label = 'com.sylvan-stack.arbol.database'
        self.domain = f'gui/{os.getuid()}'
        self.service = self.domain+'/'+self.label
        folder = places.home/'Library/Application Support/Arbol/database'
        require(value.get('Label') == self.label and value.get('WorkingDirectory') == str(folder)
                and value.get('ProgramArguments') == ['/opt/homebrew/opt/postgresql@17/bin/postgres',
                                                       '-D',str(folder/'data')],
                'The installed database launch agent differs from the expected service.')
        require(self.command('print',self.service).returncode == 0 and self.healthy(),
                'The expected database service must be loaded and healthy before the drill.')

    @staticmethod
    def command(*args: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(['/bin/launchctl',*args],stdin=subprocess.DEVNULL,capture_output=True,text=True,
                              timeout=20,check=False,env={'PATH':'/usr/bin:/bin:/usr/sbin:/sbin'})

    def healthy(self) -> bool:
        try:
            return self.inspector.read('SELECT to_json(true)',seconds=4) is True
        except DrillError:
            return False

    def stop(self) -> None:
        require(self.command('bootout',self.service).returncode == 0, 'The database launch agent could not be stopped.')
        wait_for(lambda:True if not self.healthy() else None,seconds=20,interval=0.2)

    def restore(self) -> None:
        require(hashlib.sha256(self.plist.read_bytes()).hexdigest() == self.digest,
                'The database launch-agent file changed during the drill; restoration refuses a different file.')
        if self.command('print',self.service).returncode != 0:
            require(self.command('bootstrap',self.domain,str(self.plist)).returncode == 0,
                    'The unchanged database launch agent could not be restored.')


class DirectoryWatch:
    """Observe even a fleeting run-file creation and removal between two ordinary snapshots on macOS."""

    def __init__(self, folder: Path) -> None:
        self.folder = folder
        self.fd = os.open(folder,os.O_RDONLY | os.O_NOFOLLOW)
        self.queue = select.kqueue()
        self.queue.control([select.kevent(self.fd,filter=select.KQ_FILTER_VNODE,
            flags=select.KQ_EV_ADD | select.KQ_EV_CLEAR,
            fflags=select.KQ_NOTE_WRITE | select.KQ_NOTE_RENAME | select.KQ_NOTE_DELETE)],0,0)

    def changed(self) -> bool:
        return bool(self.queue.control([],1,0))

    def close(self) -> None:
        self.queue.close()
        os.close(self.fd)


def rows(inspector: Inspector) -> Any:
    return inspector.read('SELECT json_build_object('+','.join(
        "'"+name+"',(SELECT coalesce(jsonb_agg(to_jsonb(t) ORDER BY to_jsonb(t)::text),'[]') FROM "+name+' t)'
        for name in ['chats','exchanges','messages','tool_calls','runs'])+')')


def database_away(places: Places) -> dict[str, Any]:
    calls = Commands(places)
    catalogue = calls.run('arbol-roots','list')
    require(any(root.get('root') == 'sapling' and root.get('status') == 'working' for root in catalogue),
            'First Sapling must be working before the database-away drill.')
    for root in catalogue:
        listing = calls.run('arbol-root','--root',root['root'],'list')
        require(listing.get('exchanges') == [] and listing.get('unreadable') == [],
                'A retained Root has in-progress or unreadable work; the database must stay running.')
    inspector = Inspector(places)
    service = Installed(places,inspector)
    before = rows(inspector)
    exchange = str(uuid.uuid4())
    folder = places.evidence/'outage-attempts'/exchange
    request = folder/'request.json'
    new_json(request,{'message':'This database-away check must refuse before contacting any model.',
                     'route':{'driver':'claude','subscription':'anthropic','model':'haiku'},
                     'workingFolder':str(folder)})
    new_json(folder/'before.json',before)
    watch = DirectoryWatch(places.driver/'runs')
    budget = Budget(places.evidence)
    try:
        budget.reserve(exchange)
    except BaseException:
        watch.close()
        raise
    finished = False
    try:
        run_files = sorted(path.name for path in (places.driver/'runs').iterdir())
        require(not run_files, 'A normal Claude Driver run is active; the database must stay running.')
        with stopped(stop=service.stop,restore=service.restore,healthy=service.healthy,
                     receipt=folder/'restoration.json'):
            began = time.monotonic()
            refused = calls.run('arbol-root','--root','sapling','start','trivial','--exchange',exchange,
                               '--request',str(request),seconds=20,status=1)
            elapsed = time.monotonic()-began
            new_json(folder/'refusal.json',{'elapsedSeconds':elapsed,**refused})
            require(elapsed < 15 and refused.get('error',{}).get('code') == 'database_unavailable',
                    'The stopped-database acceptance was not a bounded database_unavailable refusal.')
            exchanges = places.roots/'sapling/exchanges'
            require(not any(exchange in path.name for path in exchanges.iterdir()),
                    'The refused Exchange left a published, temporary or old Exchange folder.')
            require(not watch.changed() and not list((places.driver/'runs').iterdir()),
                    'The Claude Driver run directory changed during database-away acceptance.')
        after = rows(inspector)
        new_json(folder/'after.json',after)
        require(after == before, 'The refused Exchange changed the persisted Root rows.')
        budget.finish(exchange,'no_vendor')
        finished = True
        report = {'check':'sapling.database-away','passed':True,'exchange':exchange,'elapsedSeconds':elapsed,
                  'databaseRestored':service.healthy(),'rowsUnchanged':True,'driverRunDirectoryChanged':False,
                  'vendorRequests':0,'evidence':str(folder),'budget':budget.status()}
        new_json(folder/'qualified.json',report)
        return report
    except BaseException:
        if not finished:
            budget.finish(exchange,'ambiguous')
        raise
    finally:
        watch.close()
