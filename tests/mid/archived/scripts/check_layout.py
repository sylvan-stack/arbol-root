# Mid-tier source from scripts/check_layout.py; see MID_TIER.md.
# Shared helpers and refusal entry points remain at the original path.

# TEST-TIER-DISABLED-BEGIN scripts/check_layout.py::run_layout
# def run_layout(inputs: BuildInput, lab: SqlLab) -> dict[str, Any]:
#     files = [inputs.file(name) for name in ['chat-tables.sql', 'root-tables.sql']]
#     for file in files:
#         layout_statements(file.read_text(encoding='utf-8'))
#     database = 'layout_'+uuid.uuid4().hex
#     lab.server.createdb(database)
#     for file in files:
#         lab.run_file(database, file)
#     missing = lab.server.rows(database, COMMENTS)
#     if missing:
#         raise ValueError(f'Every table and column needs a nonempty comment: {missing}')
#     missing_sequences = lab.server.rows(database, SEQUENCE_COMMENTS)
#     if missing_sequences:
#         raise ValueError(f'Every sequence needs a nonempty comment: {missing_sequences}')
#     before = catalog(lab.server, database)
#     dumped = lab.dump(database)
#     for file in files:
#         lab.run_file(database, file)
#     if catalog(lab.server, database) != before or lab.dump(database) != dumped:
#         raise ValueError('Repeating the two layouts changed the schema.')
#     previous = check_previous(inputs, lab, database)
#     return {'check':'layout', 'root':inputs.root, 'repeated':True, 'earlierBuild':previous}
# TEST-TIER-DISABLED-END scripts/check_layout.py::run_layout

# TEST-TIER-DISABLED-BEGIN scripts/check_layout.py::main
# def main() -> int:
#     try:
#         verify(ROOT)
#         inputs = BuildInput.read(ROOT)
#         with private_server() as lab:
#             report = run_layout(inputs, lab)
#         verify(ROOT)
#         print(json.dumps(report))
#         return 0
#     except (OSError, ValueError, RuntimeError, KeyError, SqlError, subprocess.SubprocessError) as error:
#         print(f'layout check failed: {error}', file=sys.stderr)
#         return 1
# TEST-TIER-DISABLED-END scripts/check_layout.py::main

# TEST-TIER-IMPORTS-BEGIN scripts/check_layout.py:5
# import json
# TEST-TIER-IMPORTS-END scripts/check_layout.py:5

# TEST-TIER-IMPORTS-BEGIN scripts/check_layout.py:6
# import subprocess
# TEST-TIER-IMPORTS-END scripts/check_layout.py:6

# TEST-TIER-IMPORTS-BEGIN scripts/check_layout.py:8
# import uuid
# TEST-TIER-IMPORTS-END scripts/check_layout.py:8

# TEST-TIER-IMPORTS-BEGIN scripts/check_layout.py:16
# from rct_conformance.postgres import SqlError  # noqa: E402
# TEST-TIER-IMPORTS-END scripts/check_layout.py:16

# TEST-TIER-IMPORTS-BEGIN scripts/check_layout.py:17
# from rct_conformance.tables import catalog  # noqa: E402
# TEST-TIER-IMPORTS-END scripts/check_layout.py:17

# TEST-TIER-IMPORTS-BEGIN scripts/check_layout.py:19
# from scripts.layout_compatibility import check_previous  # noqa: E402
# TEST-TIER-IMPORTS-END scripts/check_layout.py:19

# TEST-TIER-IMPORTS-BEGIN scripts/check_layout.py:20
# from scripts.package_support import verify  # noqa: E402
# TEST-TIER-IMPORTS-END scripts/check_layout.py:20

# TEST-TIER-IMPORTS-BEGIN scripts/check_layout.py:21
# from scripts.sql_statements import layout_statements  # noqa: E402
# TEST-TIER-IMPORTS-END scripts/check_layout.py:21

# TEST-TIER-IMPORTS-BEGIN scripts/check_layout.py:22
# from scripts.sql_support import BuildInput, SqlLab, private_server  # noqa: E402
# TEST-TIER-IMPORTS-END scripts/check_layout.py:22

raise RuntimeError("Mid-tier checks require an explicitly requested testing task; see MID_TIER.md.")
