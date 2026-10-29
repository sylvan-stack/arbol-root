# Mid-tier source from scripts/check_migration.py; see MID_TIER.md.
# Shared helpers and refusal entry points remain at the original path.

# TEST-TIER-DISABLED-BEGIN scripts/check_migration.py::run_migration
# def run_migration(inputs: BuildInput, lab: SqlLab, older: Origin) -> dict[str,Any]:
#     names = protocol(inputs.file('migrate.sql').read_text(encoding='utf-8'))
#     source = 'from_'+uuid.uuid4().hex
#     lab.server.createdb(source)
#     for file in [older.chat,older.own]:
#         layout_statements(file.read_text(encoding='utf-8'))
#         lab.run_file(source,file)
#     seed(lab.server,source)
#     before, source_schema = rows(lab,source),catalog(lab.server,source)
#     source_counter = counter(lab.server,source) if present(lab.server,source) else None
#     original_backend = backend_rows(lab.server,source) if source_counter is not None else None
#     revisions: list[int] = []
#
#     # A server-side refusal plus the validated source protocol checks READ ONLY independently of row comparison.
#     probe = lab.server.home / 'read-only.sql'
#     probe.write_text('BEGIN ISOLATION LEVEL REPEATABLE READ READ ONLY;\nUPDATE chats SET title=title;\nCOMMIT;\n')
#     refused = lab.run_file(source,probe,single=False,check=False)
#     probe.unlink()
#     if refused.returncode != 3 or 'read-only' not in refused.stderr:
#         raise ValueError('The private READ ONLY write probe did not refuse with status 3.')
#     unchanged(before,rows(lab,source))
#
#     def target() -> str:
#         database = 'to_'+uuid.uuid4().hex
#         lab.server.createdb(database)
#         for name in ['chat-tables.sql','root-tables.sql']:
#             file = inputs.file(name)
#             layout_statements(file.read_text(encoding='utf-8'))
#             lab.run_file(database,file)
#         return database
#
#     def success() -> tuple[Rows,set[str]]:
#         database = target()
#         shape = catalog(lab.server,database)
#         began = timestamp(lab.server.value(source,'SELECT to_json(clock_timestamp())'))
#         answer = invoke(lab,inputs,source,database,names)
#         ended = timestamp(lab.server.value(database,'SELECT to_json(clock_timestamp())'))
#         if answer.returncode:
#             raise ValueError(f'psql migration ended with {answer.returncode}: {answer.stderr.strip()}')
#         unchanged(before,rows(lab,source))
#         if source_counter is not None and counter(lab.server,source) != source_counter:
#             raise ValueError('Whole migration changed the original Draft counter.')
#         if original_backend is not None and (backend_rows(lab.server,source) != original_backend
#                                             or backend_rows(lab.server,database) != original_backend):
#             raise ValueError('Whole migration changed exact backend text/JSON/rows.')
#         if catalog(lab.server,source) != source_schema or catalog(lab.server,database) != shape:
#             raise ValueError('Migration changed a source or destination table layout.')
#         actual = rows(lab,database)
#         opened = judge(before,actual,older.root,began,ended)
#         if source_counter is not None:
#             revisions.append(next_draft(lab.server,database,source_counter,
#                                        max(row['revision'] for row in before['public.drafts'])))
#         return actual,opened
#
#     first,opened = success()
#     for missing in ['source','table']:
#         database = target()
#         target_counter = counter(lab.server,database) if source_counter is not None else None
#         from_database = source
#         if missing == 'source':
#             from_database = 'absent_'+uuid.uuid4().hex
#         else:
#             lab.server.execute(database,'DROP TABLE migrated_chats')
#         answer = invoke(lab,inputs,from_database,database,names)
#         if answer.returncode != 3 or any(rows(lab,database).values()):
#             raise ValueError(f'The missing-{missing} migration must exit 3 and leave no destination row.')
#         unchanged(before,rows(lab,source))
#         if target_counter is not None and counter(lab.server,database) != target_counter:
#             raise ValueError('A failed migration changed the target Draft counter.')
#     second,second_opened = success()
#     if normalized(first,opened) != normalized(second,second_opened):
#         raise ValueError('A fresh repeated migration differs beyond the snapshot times.')
#     report = {'check':'migration','root':inputs.root,'olderRoot':older.root,'sourceUnchanged':True,
#             'unchangedTables':len(before),'sourceRows':sum(map(len,before.values())),
#             'interruptedExchanges':len(opened),'provenanceRows':len(before['public.chats']),
#             'missingSourceStatus':3,'missingTableStatus':3,'repeatable':True}
#     if source_counter is not None:
#         report['backendTables'] = {'exact':True,'sourceCounterUnchanged':True,'savedNextRevisions':revisions}
#     return report
# TEST-TIER-DISABLED-END scripts/check_migration.py::run_migration

# TEST-TIER-DISABLED-BEGIN scripts/check_migration.py::check_migration
# def check_migration(inputs: BuildInput, *, home: Path | None = None) -> dict[str,Any]:
#     if inputs.older is None:
#         return {'check':'migration','root':inputs.root,'olderRoot':None,'serverNeeded':False}
#     older = origin(inputs,home or Path.home())
#     script = inputs.file('migrate.sql').read_text(encoding='utf-8')
#     protocol(script)
#     for mode in inputs.modes:
#         mode_protocol(script,mode)
#     with private_server() as lab:
#         report = run_migration(inputs,lab,older)
#         if inputs.modes:
#             report['optionalModes'] = check_modes(inputs,lab)
#         return report
# TEST-TIER-DISABLED-END scripts/check_migration.py::check_migration

# TEST-TIER-DISABLED-BEGIN scripts/check_migration.py::main
# def main() -> int:
#     try:
#         verify(ROOT)
#         report = check_migration(BuildInput.read(ROOT))
#         verify(ROOT)
#         print(json.dumps(report))
#         return 0
#     except (OSError,ValueError,RuntimeError,KeyError,SqlError,subprocess.SubprocessError) as error:
#         print(f'migration check failed: {error}',file=sys.stderr)
#         return 1
# TEST-TIER-DISABLED-END scripts/check_migration.py::main

# TEST-TIER-IMPORTS-BEGIN scripts/check_migration.py:11
# import uuid
# TEST-TIER-IMPORTS-END scripts/check_migration.py:11

# TEST-TIER-IMPORTS-BEGIN scripts/check_migration.py:21
# from rct_conformance.postgres import SqlError  # noqa: E402
# TEST-TIER-IMPORTS-END scripts/check_migration.py:21

# TEST-TIER-IMPORTS-BEGIN scripts/check_migration.py:22
# from rct_conformance.tables import catalog  # noqa: E402
# TEST-TIER-IMPORTS-END scripts/check_migration.py:22

# TEST-TIER-IMPORTS-BEGIN scripts/check_migration.py:26
# from scripts.backend_tables import counter, next_draft, present  # noqa: E402
# TEST-TIER-IMPORTS-END scripts/check_migration.py:26

# TEST-TIER-IMPORTS-BEGIN scripts/check_migration.py:27
# from scripts.backend_tables import rows as backend_rows  # noqa: E402
# TEST-TIER-IMPORTS-END scripts/check_migration.py:27

# TEST-TIER-IMPORTS-BEGIN scripts/check_migration.py:28
# from scripts.chat_migration_check import check_modes  # noqa: E402
# TEST-TIER-IMPORTS-END scripts/check_migration.py:28

# TEST-TIER-IMPORTS-BEGIN scripts/check_migration.py:30
# from scripts.migration_fixtures import seed  # noqa: E402
# TEST-TIER-IMPORTS-END scripts/check_migration.py:30

# TEST-TIER-IMPORTS-BEGIN scripts/check_migration.py:31
# from scripts.migration_protocol import mode_protocol, protocol  # noqa: E402
# TEST-TIER-IMPORTS-END scripts/check_migration.py:31

# TEST-TIER-IMPORTS-BEGIN scripts/check_migration.py:32
# from scripts.package_support import verify  # noqa: E402
# TEST-TIER-IMPORTS-END scripts/check_migration.py:32

# TEST-TIER-IMPORTS-BEGIN scripts/check_migration.py:33
# from scripts.sql_statements import layout_statements  # noqa: E402
# TEST-TIER-IMPORTS-END scripts/check_migration.py:33

# TEST-TIER-IMPORTS-BEGIN scripts/check_migration.py:34
# from scripts.sql_support import BuildInput, SqlLab, private_server, regular  # noqa: E402
# TEST-TIER-IMPORTS-END scripts/check_migration.py:34

raise RuntimeError("Mid-tier checks require an explicitly requested testing task; see MID_TIER.md.")
