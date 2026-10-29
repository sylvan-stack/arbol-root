# Mid-tier source from scripts/verify_sql_build.py; see MID_TIER.md.
# Shared helpers and refusal entry points remain at the original path.

# TEST-TIER-DISABLED-BEGIN scripts/verify_sql_build.py
# """Qualify both Root SQL Build paths in a disposable home and registry."""
#
# from __future__ import annotations
#
# import argparse
# import hashlib
# import json
# import os
# import re
# import shutil
# import stat
# import subprocess
# import sys
# import tempfile
# from pathlib import Path
# from typing import Any
#
# ROOT = Path(__file__).resolve().parents[1]
# sys.path.insert(0,str(ROOT))
# from scripts.package_support import write_manifest  # noqa: E402
# from scripts.sql_support import tools  # noqa: E402
#
#
# def fixture_source(source: Path, destination: Path) -> Path:
#     tracked = subprocess.run(['git','ls-files','-z'],cwd=source,capture_output=True,check=True).stdout
#     destination.mkdir()
#     for name in tracked.decode().split('\0'):
#         if name:
#             target = destination / name
#             target.parent.mkdir(parents=True,exist_ok=True)
#             shutil.copy2(source / name,target)
#     root = destination / 'roots/fictionalnew'
#     root.mkdir()
#     for name in ['layout.sql','migrate.sql']:
#         shutil.copy2(destination / 'tests/fixtures/migration-root' / name,root / name)
#     for arguments in [['init','-q','-b','main'],['add','--all'],['commit','-qm','Private SQL Build fixture']]:
#         subprocess.run(['git',*arguments],cwd=destination,capture_output=True,check=True)
#     return destination
#
#
# def qualify(source: Path, tool: Path, cache: Path, output: Path, selected: str | None,
#             previous: Path | None = None) -> dict[str,Any]:
#     source,tool,cache,output = source.resolve(),tool.resolve(),cache.resolve(),output.resolve()
#     if output.exists():
#         raise ValueError('The evidence folder must be new.')
#     output.mkdir(parents=True)
#     dirty = subprocess.run(['git','status','--porcelain'],cwd=source,capture_output=True,text=True,check=True)
#     if dirty.stdout:
#         raise ValueError('Commit the qualification source before building it.')
#     original = source
#     found = tools(os.environ.get('PATH',os.defpath))
#     oracle = source / 'contract/conformance/specifications/03-the-chat-tables.md'
#     if not oracle.is_file():
#         oracle = Path.home() / 'Artifacts/arbol-root/contract/03-the-chat-tables.md'
#     with tempfile.TemporaryDirectory(prefix='root-sql-build-') as temporary:
#         home = Path(temporary).resolve()
#         if selected is None:
#             source = fixture_source(source,home / 'fictional source')
#             selected = 'fictionalnew'
#         if not re.fullmatch('[a-z0-9]+',selected) or selected == 'sapling':
#             raise ValueError('The descendant needs a distinct lowercase Root identifier.')
#         env = {'HOME':str(home),'PATH':os.environ.get('PATH',os.defpath),'LANG':'en_US.UTF-8',
#                'ARBOL_PYTHON_ARCHIVE_CACHE':str(cache)}
#         oracle_copy = home / 'Artifacts/arbol-root/contract/03-the-chat-tables.md'
#         oracle_copy.parent.mkdir(parents=True)
#         shutil.copy2(oracle,oracle_copy)
#         roots = home / 'Library/Application Support/Arbol/roots'
#         for name in ['sapling',selected]:
#             folder = roots / name
#             folder.mkdir(parents=True)
#             record = {'root':name,'rootContract':1,'status':'working' if name=='sapling' else 'preparing',
#                       'createdAt':'2026-10-26T09:00:00.000Z'}
#             if name != 'sapling':
#                 record['grewFrom'] = 'sapling'
#             (folder / 'root.json').write_text(json.dumps(record))
#         registry,bin_dir = home / 'registry with spaces',home / '.local/bin'
#         reports: dict[str,Any] = {}
#         previous_number: str | None = None
#         for name in ['sapling',selected]:
#             if name==selected and previous is not None:
#                 record = json.loads((previous/'build.json').read_bytes())
#                 manifest = json.loads((previous/'package-manifest.json').read_bytes())
#                 if record.get('root')!=selected or record.get('status')!='working' or 'prunedAt' in record:
#                     raise ValueError('The earlier comparison Build must be a retained working Build of this Root.')
#                 previous_number = record['build']
#                 saved = registry/'arbol-root'/previous_number
#                 saved.mkdir(parents=True)
#                 for relative in ['build.json','package.json','layout/chat-tables.sql','layout/root-tables.sql']:
#                     file = previous/relative
#                     if not stat.S_ISREG(file.lstat().st_mode):
#                         raise ValueError('The earlier Build comparison input is not regular.')
#                     data = file.read_bytes()
#                     if relative.startswith('layout/') and hashlib.sha256(data).hexdigest()!=manifest['files'].get(relative):
#                         raise ValueError('The earlier Build SQL no longer matches its qualified manifest.')
#                     destination = saved/relative
#                     destination.parent.mkdir(parents=True,exist_ok=True)
#                     destination.write_bytes(data)
#             print(f'Building private Root {name}' ,file=sys.stderr,flush=True)
#             answer = subprocess.run([str(tool),'build','arbol-root','--root',name,'--repo',str(source),
#                                      '--registry-dir',str(registry),'--bin-dir',str(bin_dir)],
#                                     env=env,capture_output=True,text=True,check=False,timeout=600)
#             (output / (name+'-reply.json')).write_text(answer.stdout)
#             value = json.loads(answer.stdout)
#             folder = registry / 'arbol-root' / value['build']
#             log = (folder / 'build.log').read_text()
#             (output / (name+'-build.log')).write_text(log)
#             if (answer.returncode or value.get('status') != 'working'
#                     or value.get('checks') != [{'name':check,'passed':True} for check in ['unit','layout','migration']]
#                     or re.search(r'skipped=\d+',log)):
#                 raise ValueError(f'The private {name} Build failed; see {output}.')
#             if name==selected and previous_number is not None:
#                 layouts = [json.loads(line) for line in log.splitlines() if line.startswith('{"check": "layout"')]
#                 if len(layouts)!=1 or layouts[0].get('earlierBuild')!=previous_number:
#                     raise ValueError('The actual private Build did not qualify the retained earlier layout.')
#             manifest = json.loads((folder / 'package-manifest.json').read_text())
#             (output / (name+'-manifest.json')).write_text(json.dumps(manifest,indent=2)+'\n')
#             listed = subprocess.run([str(folder / 'bin/arbol-root'),'list'],env=env,cwd=home,
#                                     capture_output=True,text=True,check=True,timeout=15)
#             if json.loads(listed.stdout) != {'root':name,'rootBuild':value['build'],'rootPackageVersion':'1.0.0',
#                                              'exchanges':[],'unreadable':[]}:
#                 raise ValueError('The real packaged manager did not retain its adjacent Root/Build identity.')
#             reports[name] = {'build':value['build'],'checks':value['checks'],
#                              'unitSummaries':re.findall(r'Ran \d+ tests in [\d.]+s',log),'source':manifest['source'],
#                              'packagedListingIdentity':True}
#         # A copied candidate keeps the real earlier working descendant in the registry.
#         earlier = registry / 'arbol-root' / reports[selected]['build']
#         number = format(int(earlier.name,16)+1,'x')
#         candidate = earlier.parent / number
#         shutil.copytree(earlier,candidate)
#         record = json.loads((candidate / 'build.json').read_text())
#         record.update(build=number,status='building')
#         (candidate / 'build.json').write_text(json.dumps(record))
#         manifest = json.loads((candidate / 'package-manifest.json').read_text())
#         manifest['build'] = number
#         (candidate / 'package-manifest.json').write_text(json.dumps(manifest))
#         python = candidate / 'runtime/python/bin/python3.14'
#
#         def check(label: str, *, succeeds: bool, environment: dict[str,str] | None = None,
#                   script: str = 'check_layout.py',message: str | None = None) -> dict[str,Any] | None:
#             write_manifest(candidate)
#             answer = subprocess.run([str(python),'-I','-B',str(candidate / 'scripts' / script)],
#                                     env=environment or env,capture_output=True,text=True,check=False,timeout=120)
#             (output / (label+'.txt')).write_text(answer.stdout+answer.stderr)
#             if answer.returncode != (0 if succeeds else 1) or (message and message not in answer.stderr):
#                 raise ValueError(f'The packaged {label} probe had an unexpected result; see {output}.')
#             return json.loads(answer.stdout) if succeeds else None
#
#         repeated = check('earlier-working-build',succeeds=True)
#         if repeated is None or repeated.get('earlierBuild') != earlier.name:
#             raise ValueError('The packaged layout check did not compare the earlier working Root Build.')
#         own = candidate / 'layout/root-tables.sql'
#         original_sql = own.read_text()
#         changed,count = re.subn(r"(COMMENT ON TABLE\s+\w+\s+IS\s+')",r'\1Edited fixture. ',original_sql,count=1,
#                                flags=re.IGNORECASE)
#         if count != 1:
#             raise ValueError('The descendant layout needs its prescribed table comment.')
#         own.write_text(changed)
#         check('edited-earlier-statement',succeeds=False,message='complete statement of the earlier Build')
#         own.write_text(original_sql+"\nALTER TABLE chats ADD COLUMN IF NOT EXISTS fixture_required integer NOT NULL;\n"
#                        "COMMENT ON COLUMN chats.fixture_required IS 'Fictional incompatible addition';\n")
#         check('required-column-without-default',succeeds=False,message='NOT NULL column without a default')
#         own.write_text(original_sql)
#         for missing in found:
#             search = home / ('without-'+missing)
#             search.mkdir()
#             for name,program in found.items():
#                 if name != missing:
#                     (search / name).symlink_to(program)
#             check('missing-'+missing,succeeds=False,environment={**env,'PATH':str(search)},message=missing)
#         # No-lineage passes before PostgreSQL preflight, through the actual packaged entry.
#         first = registry / 'arbol-root' / reports['sapling']['build']
#         answer = subprocess.run([str(first / 'runtime/python/bin/python3.14'),'-I','-B',
#                                  str(first / 'scripts/check_migration.py')],
#                                 env={**env,'PATH':str(home / 'absent')},capture_output=True,text=True,check=True,timeout=30)
#         fast = json.loads(answer.stdout)
#         if fast.get('serverNeeded') is not False:
#             raise ValueError('The no-lineage packaged entry did not pass before tool discovery.')
#         return {'check':'root.private-sql-builds','fixtureOnly':source != original,'roots':reports,
#                 'earlierWorkingBuild':earlier.name,'retainedEarlierBuild':previous_number,'editedStatementRejected':True,'requiredColumnRejected':True,
#                 'missingToolsNamed':list(found),'noLineageWithoutTools':True,'ownerRootsChanged':False,
#                 'vendorRequests':0,'temporaryStateRemovedOnReturn':True}
#
#
# def main() -> int:
#     parser = argparse.ArgumentParser(description=__doc__)
#     parser.add_argument('--source',type=Path,default=ROOT)
#     parser.add_argument('--tool',type=Path,default=Path.home() / '.local/bin/arbol-builds')
#     parser.add_argument('--cache',type=Path,default=Path.home() / '.cache/arbol-driver-build/python')
#     parser.add_argument('--output',type=Path,required=True)
#     parser.add_argument('--previous-root-build',type=Path)
#     choice = parser.add_mutually_exclusive_group(required=True)
#     choice.add_argument('--fixture',action='store_true')
#     choice.add_argument('--root')
#     args = parser.parse_args()
#     report = qualify(args.source,args.tool,args.cache,args.output,args.root,args.previous_root_build)
#     (args.output / 'report.json').write_text(json.dumps(report,indent=2)+'\n')
#     print(json.dumps(report,indent=2))
#     return 0
#
#
# if __name__ == '__main__':
#     raise SystemExit(main())
# TEST-TIER-DISABLED-END scripts/verify_sql_build.py


raise RuntimeError("Mid-tier checks require an explicitly requested testing task; see MID_TIER.md.")
