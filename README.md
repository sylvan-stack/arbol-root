# Arbol Root

Arbol Root: a component of Arbol 2.

It holds the Root Contract's chat tables, `contract/1/layout.sql`, and its conformance suite, `contract/conformance/` (see its [README](contract/conformance/README.md)). The Root manager provides `trunks`, `start`, `list`, `stop` and `settle`: compatible Trunk inventory, exact-Build detached acceptance, record-only Exchange listing, verified group stopping and delegated persistence.

| | |
|---|---|
| Package | `@sylvan-stack/arbol-root` 1.0.0 |
| Artifact corpus | `~/Artifacts/arbol-root` (GitHub `sylvan-stack/arbol-root-artifacts`) |

## Root manager development and Builds

Run `uv sync --locked --group dev` once. `bin/arbol-root --root <root> trunks` runs the development program (Build 0); a packaged program reads its Root from its adjacent Build record. It reads no settings file or database. `start` passes on a request without opening it, removes its name after a reply and leaves it and the process alone on `no_answer`. `list` reads only Exchange records and checks each PID/start time in a clean C/UTC environment. `--root-dir` requires `--bin-dir`, pointing tests at a private Root and a stand-in launcher.

`arbol-builds build arbol-root --root <root>` packages checksum-pinned standalone CPython 3.14.8, the standard-library manager, its tests and the conformance suite. The final build command reads the Root record under HOME and copies its version's chat layout, its own layout, and a migration script only when it grew from another Root. A missing required file fails the Build. Only `unit` is defined at this stage; layout and migration qualification follow in SYL-184. No Root on this Mac is created by building the program.

`stop <UUID>` appends one stop line to an existing regular control file, then observes the record. `stop --force <UUID>`, or a graceful stop still running after 20 awake seconds, verifies the recorded group leader and sends TERM, then KILL after five seconds when verified members remain. Another five seconds with survivors gives `not_ended`. PID/start-time identities protect against reused processes and remain anchored by surviving group members after a leader exits. macOS deadlines use `CLOCK_UPTIME_RAW`, excluding sleep. Unknown records, ownership or control writes refuse safely. A gone process is settled; a persistence refusal is included in the successful stop's result without claiming the data was saved.

`settle [<UUID>]` delegates to an exact chosen compatible Build of the Trivial Trunk. Without a UUID it visits dead records in lexical order and stops on `database_unavailable`; an empty pass needs no launcher. It also removes real UUID `.old` folders and `.new` folders strictly older than 15 seconds with a verified dead process or no record. Living, young and unverifiable new folders stay; named settle and stop do no dot cleanup. The manager never reads event, route or request payloads, connects to a database or keeps state between commands.

The unit check verifies the complete file manifest (excluding mutable Build records/logs/last-start and Python caches), runs both test families with its own interpreter and verifies integrity again. Tests use fictional records, private homes, scripted launchers and, for the unchanged conformance-suite tests, private socket-only PostgreSQL servers. They use no account or vendor request.

`scripts/verify_build.py` qualifies a disposable packaged manager through real Build Tool launchers, including stop, exact-Trivial-Build settling and dot cleanup. Its packaged unit suite includes real private TERM/ignored-TERM groups and a surviving child, plus an in-process moved clock for the full 20/5/5-second escalation and `not_ended`. Real-Root operational drills remain SYL-188. No global Root manager is installed until the First Roots work supplies its real Root.

```sh
uv run --no-sync python -B -m unittest discover -s tests -t tests
uv run --no-sync python -B -m unittest discover -s contract/conformance/tests -t contract/conformance
uv run --no-sync ruff check .
uv run --no-sync mypy
uv run --no-sync python -B scripts/verify_build.py
```

## Sylvan Stack 2

| Repository | Package | Version | Artifact corpus | Artifact repository |
|---|---|---|---|---|
| `arbol` | `@sylvan-stack/arbol` | 2.0.0 | `~/Artifacts/arbol` | `sylvan-stack/arbol-artifacts` |
| `arbol-root` | `@sylvan-stack/arbol-root` | 1.0.0 | `~/Artifacts/arbol-root` | `sylvan-stack/arbol-root-artifacts` |
| `arbol-trunk` | `@sylvan-stack/arbol-trunk` | 1.0.0 | `~/Artifacts/arbol-trunk` | `sylvan-stack/arbol-trunk-artifacts` |
| `arbol-claude-driver` | `@sylvan-stack/arbol-claude-driver` | 1.0.0 | `~/Artifacts/arbol-claude-driver` | `sylvan-stack/arbol-claude-driver-artifacts` |
| `arbol-codex-driver` | `@sylvan-stack/arbol-codex-driver` | 1.0.0 | `~/Artifacts/arbol-codex-driver` | `sylvan-stack/arbol-codex-driver-artifacts` |
| `mycel` | `@sylvan-stack/mycel` | 2.0.0 | `~/Artifacts/mycel` | `sylvan-stack/mycel-artifacts` |
| `arbol-pi-driver` | `@sylvan-stack/arbol-pi-driver` | 1.0.0 | `~/Artifacts/arbol-pi-driver` | `sylvan-stack/arbol-pi-driver-artifacts` |
| `workspace-ledger` | `workspace-ledger` (planned) | 1.0.0 | `~/Artifacts/sylvan-stack/repos/workspace-ledger` | `sylvan-stack/workspace-ledger-artifacts` |
