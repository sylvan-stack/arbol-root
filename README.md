# Arbol Root

Arbol Root: a component of Arbol 2.

It holds the Root Contract's chat tables, `contract/1/layout.sql`, and its conformance suite, `contract/conformance/` (see its [README](contract/conformance/README.md)). The Root manager provides `trunks`, `start`, `list`, `stop` and `settle`: compatible Trunk inventory, exact-Build detached acceptance, record-only Exchange listing, verified group stopping and delegated persistence.

| | |
|---|---|
| Package | `@sylvan-stack/arbol-root` 1.0.0 |
| Artifact corpus | `~/Artifacts/arbol-root` (GitHub `sylvan-stack/arbol-root-artifacts`) |

## Root manager development and Builds

Run `uv sync --locked --group dev` once. `bin/arbol-root --root <root> trunks` runs the development program (Build 0); a packaged program reads its Root from its adjacent Build record. It reads no settings file or database. `start` passes on a request without opening it, removes its name after a reply and leaves it and the process alone on `no_answer`. `list` reads only Exchange records and checks each PID/start time in a clean C/UTC environment. `--root-dir` requires `--bin-dir`, pointing tests at a private Root and a stand-in launcher.

`arbol-builds build arbol-root --root <root>` packages checksum-pinned standalone CPython 3.14.8, the standard-library manager, its tests and the conformance suite. The final build command reads the Root record under HOME and copies its version's chat layout, its own layout, and a migration script only when it grew from another Root. A missing required file fails the Build. Its three checks are `unit`, `layout` and `migration`. No Root on this Mac is created by building the program.

`stop <UUID>` appends one stop line to an existing regular control file, then observes the record. `stop --force <UUID>`, or a graceful stop still running after 20 awake seconds, verifies the recorded group leader and sends TERM, then KILL after five seconds when verified members remain. Another five seconds with survivors gives `not_ended`. PID/start-time identities protect against reused processes and remain anchored by surviving group members after a leader exits. macOS deadlines use `CLOCK_UPTIME_RAW`, excluding sleep. Unknown records, ownership or control writes refuse safely. A gone process is settled; a persistence refusal is included in the successful stop's result without claiming the data was saved.

`settle [<UUID>]` delegates to an exact chosen compatible Build of the Trivial Trunk. Without a UUID it visits dead records in lexical order and stops on `database_unavailable`; an empty pass needs no launcher. It also removes real UUID `.old` folders and `.new` folders strictly older than 15 seconds with a verified dead process or no record. Living, young and unverifiable new folders stay; named settle and stop do no dot cleanup. The manager never reads event, route or request payloads, connects to a database or keeps state between commands.

The unit check verifies the complete file manifest (excluding mutable Build records/logs/last-start and Python caches), runs both test families with its own interpreter and verifies integrity again. Tests use fictional records, private homes, scripted launchers and, for the unchanged conformance-suite tests, private socket-only PostgreSQL servers. They use no account or vendor request.

The layout check runs both copied files twice on its own temporary PostgreSQL server, requires table/column comments and compares the catalogue and schema-only dump. Against the newest earlier working, unpruned Build of that Root still carrying its SQL, it preserves whole earlier statements and objects, rejects incompatible additions to old tables, and requires the earlier-then-new schema to equal a fresh schema. Layouts permit plain table, column, index and comment DDL. The SQL helpers preflight `initdb`, `pg_ctl`, `createdb`, `psql` and `pg_dump`, ignore inherited PostgreSQL settings and remove their socket-only server afterwards.

The migration check passes immediately without a server for a Root with no lineage. Otherwise, on a separate private server, it builds the older schema from packaged SQL and seeds fictional chats with completed, failed, cancelled and open Exchanges, replacement history and exact Unicode/text/JSON payloads. The copied migration must use the prescribed read-only repeatable source snapshot and one destination transaction. The check verifies every old row, snapshot interruption, provenance, source immutability, status 3 and empty destinations for the two required failures, and a fresh repeat. It runs no SQL against the owner's database. Applying layouts or migrating a real Root remains `arbol-roots` work and the SYL-189 drill.

`scripts/verify_build.py` qualifies a disposable packaged manager through real Build Tool launchers, including stop, exact-Trivial-Build settling and dot cleanup. Its packaged unit suite includes real private TERM/ignored-TERM groups and a surviving child, plus an in-process moved clock for the full 20/5/5-second escalation and `not_ended`. Real-Root operational drills remain SYL-188. No global Root manager is installed until the First Roots work supplies its real Root.

`scripts/verify_sql_build.py --fixture --output <private-evidence-folder>` builds First Sapling and an explicitly fictional descendant through the installed Build Tool, with all three checks. Only its disposable source copy gets `roots/fictionalnew`; this is not the second production Root's identity. It then invokes the packaged checks against an earlier working Build, with edited-statement and NOT NULL faults, and with each mandatory tool missing. Use `--root <owner-given-identifier>` instead of `--fixture` once that Root's production files exist. All homes, registries, databases and source fixtures are removed; the requested evidence folder retains reports and Build logs outside Git.

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
