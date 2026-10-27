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

The unit check verifies the complete file manifest (excluding mutable Build records/logs/last-start and Python caches), runs both test families with its own interpreter and verifies integrity again. Tests use fictional records, private homes, scripted launchers and, for the unchanged conformance-suite tests, private socket-only PostgreSQL servers. CLI fixtures copy their own development image from the checked files, so their fictional Root does not conflict with the enclosing Build's identity. Adjacent numbered-Build identity has separate checks and both private SQL Builds run the real packaged listing. They use no account or vendor request.

The layout check runs both copied files twice on its own temporary PostgreSQL server, requires table/column comments and compares the catalogue and schema-only dump. Against the newest earlier working, unpruned Build of that Root still carrying its SQL, it preserves whole earlier statements and objects, rejects incompatible additions to old tables, and requires the earlier-then-new schema to equal a fresh schema. Layouts permit plain table, column, index and comment DDL. The SQL helpers preflight `initdb`, `pg_ctl`, `createdb`, `psql` and `pg_dump`, ignore inherited PostgreSQL settings and remove their socket-only server afterwards.

The migration check passes immediately without a server for a Root with no lineage. Otherwise, on a separate private server, it builds the older schema from packaged SQL and seeds fictional chats with completed, failed, cancelled and open Exchanges, replacement history and exact Unicode/text/JSON payloads. The copied migration must use the prescribed read-only repeatable source snapshot and one destination transaction. The check verifies every old row, snapshot interruption, provenance, source immutability, status 3 and empty destinations for the two required failures, and a fresh repeat. It runs no SQL against the owner's database. Applying layouts or migrating a real Root remains `arbol-roots` work and the SYL-189 drill.

`scripts/verify_build.py` qualifies a disposable packaged manager through real Build Tool launchers, including stop, exact-Trivial-Build settling and dot cleanup. Its packaged unit suite includes real private TERM/ignored-TERM groups and a surviving child, plus an in-process moved clock for the full 20/5/5-second escalation and `not_ended`. The operational stopping drills below qualify retained First Sapling separately from automatic Build checks. SYL-186 installs the real First Sapling manager from merged readonly source.

`scripts/verify_sql_build.py --fixture --output <private-evidence-folder>` builds First Sapling and an explicitly fictional descendant through the installed Build Tool, with all three checks. Only its disposable source copy gets `roots/fictionalnew`; this is not the second production Root's identity. It then invokes the packaged checks against an earlier working Build, with edited-statement and NOT NULL faults, and with each mandatory tool missing. Use `--root <owner-given-identifier>` instead of `--fixture` once that Root's production files exist. All homes, registries, databases and source fixtures are removed; the requested evidence folder retains reports and Build logs outside Git.

```sh
uv run --no-sync python -B -m unittest discover -s tests -t tests
uv run --no-sync python -B -m unittest discover -s contract/conformance/tests -t contract/conformance
uv run --no-sync ruff check .
uv run --no-sync mypy
uv run --no-sync python -B scripts/verify_build.py
```

## First Roots operational drills

`roots/sapling/drills/make-sapling.py` creates only an absent First Sapling and builds its manager from clean merged `readonly/arbol-root`. It records each phase and refuses to replay creation over retained data. The real Root's private directory, settings, database and Build remain after success.

`roots/sapling/drills/real-messages.py` only preflights by default. `--send` submits two Haiku messages through the normal owner `anthropic` Subscription, checks acceptance/listing, remembered context and persisted answers/usage, and records each attempt before submission. The private locked ledger enforces the owner's shared ten-message allowance across SYL-186–189. An ambiguous attempt still counts; inspect its evidence before any new submission. A known rate-limit deadline blocks fresh submissions even when a cached usage report shows capacity. These commands write normal Claude session state when sending. They never switch Subscriptions or routes after a refusal.

`roots/sapling/drills/database-away.py` requires no active or unreadable Exchange in any retained Root and no normal Claude Driver run. It stops only the expected installed database launch agent, checks a bounded acceptance refusal with no folder, run or row changes, then restores the unchanged launch agent and proves health. Catchable SIGINT/SIGTERM also restore it; SIGKILL and machine power loss cannot run cleanup. Private-server tests prove success, failure, partial-stop and signal restoration before the operational drill is run.

All receipts, requests, rows and reported costs stay outside Git under `~/.local/share/arbol-root-evidence/first-roots/`, with private permissions and unique attempt directories. Reports never infer a price when the Driver omits cost. Unit discovery uses only private homes and servers, without an account or vendor call. Run operational scripts explicitly with `uv run --no-sync python <script>`; creation, real messages and stopping the installed service are never automatic Build checks.

The `drill-*.py` scripts preflight by default; `--run` performs their named operation against retained First Sapling. `run-trunk-drills.py --run` runs the eight deterministic drills in order and stops on the first failure. These use a temporary Driver home, the existing RCT-4 stand-in and a byte-identical copy of the installed Trunk launcher through `--bin-dir`. Their Driver wrapper has an empty environment with only its private HOME, fixed interpreter and system path; it reads no owner credential or normal Driver state. Each run checks the unchanged pre-existing Root rows, an empty final Exchange directory and restored database health, and preserves the new drill history.

| Script under `roots/sapling/drills/` | What it proves |
|---|---|
| `drill-trunk-killed.py` | A verified owned Trunk killed mid-run lists/settles interrupted and its chat continues; whole answer blocks, open calls and last usage follow RCT-3 |
| `drill-trunk-hangs.py` | The actual sixty-second self-watch ends hung work, its Driver and stand-in child, then settling recovers it |
| `drill-starter-gone.py` | The detached Exchange completes after its owned starter and pseudo-terminal disappear |
| `drill-database-away-mid-run.py` | Output and heartbeat continue offline, then pending ordered rows are saved before the run finishes |
| `drill-database-away-through-end.py` | The actual sixty-second final retry leaves a completed unsaved folder, then settling recovers it after restoration |
| `drill-folder-unwritable.py` | The Exchange fails truthfully, its running call stops, permissions are restored and settling preserves the saved failure |
| `drill-failed-exchange.py`, `drill-cancelled-exchange.py` | One failed/cancelled chat resumes while another chat continues independently |

Only `drill-trunk-killed.py --run --real` makes a real vendor submission. It uses one approved Haiku message and the shared durable allowance; inspect an existing attempt before any later explicit run. Its ordinary form and the aggregate runner make none. A killed run can report no usage or cost before its end is cut off; missing values stay unknown. RCT-3 persists whole top-level `text` events and deliberately discards `text_delta` fragments after settling. The saved raw events remain in private evidence, and the drill never invents a message row from them. Database outages and permission changes restore through catchable interruptions; an unclean owned process or uncertain result prevents a successful verdict.

The stopping scripts also require `--run` and never submit a vendor request. `drill-stop-obeyed.py` checks graceful cancellation and chat continuation; `drill-stop-not-obeyed.py` freezes the verified Trunk and observes the actual twenty-second wait and force; `drill-stop-force.py` and `drill-stop-force-ignored-term.py` verify group cleanup and the actual five-second grace. `drill-root-killed-while-waiting.py` and `drill-root-killed-while-forcing.py` kill only their own manager command and verify a new command recovers the record/group as found. Freeze guards always thaw the same surviving PID/start identity after failures or catchable signals, and never resume a reused PID. The ignored child exists only in its private Driver home and the owned Trunk group.

`drill-stop-end-already-written.py` follows the accepted manager contract: it freezes a Trunk with a known completed end during a database outage, restores the service, verifies an immediate unforced reply with no new control line, then thaws it to save. It does not force work that already has its end. A graceful reply can say `saved` when the folder disappeared before the manager saw the end; the drills also inspect the persisted final state.

`drill-newer-build.py --run` explicitly makes a newer First Sapling manager from clean merged `readonly/arbol-root` while an Exchange is running, requires all three packaged checks, and uses that manager to list, stop and settle without changing Root identity. Every qualified receipt is retained in private evidence. `--run --reuse-qualified` verifies the retained working Build, exact source/check record and chosen Build against the last receipt without building again. `run-stopping-drills.py --run` runs all eight deterministic cases and uses that receipt for the newer-Build case; run the explicit Build drill first. A changed, failed, unchosen or incomplete Build refuses reuse.

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

The Jensen migration phases are explicit and retain their history under private `second-root-attempts/`, `jensen-drills/` and `trunk-drills/jensen-*/` evidence folders. Run them in order: `make-second-root.py --run` creates **Jensen Root** (`jensen`) from Sapling and qualifies its manager from merged readonly source; `drill-migration-fails.py --run` proves a bounded mid-copy refusal with the installed database fully stopped and restored; `drill-migration-open-exchange.py --run` retries while an owned Sapling Exchange remains open, checks exact copied rows/provenance, then lets the original finish only in Sapling; `second-root-ready.py --run` makes Jensen current and checks default selection, continued Sapling use and refusal to migrate a working Root.

`migrated-chat-goes-on.py --run` checks the migrated successful real chat through a private stand-in and compares the single Driver **run** request with its saved history; discovery calls are separate records. `--run --send` then allows one real Haiku continuation on the normal owner Subscription, with reservation before submission, no automatic retry, remembered context, persisted usage and reported cost. The shared message ledger and any recorded retry deadline still apply. Inspect a failed or ambiguous receipt before another explicit operation. The narrowly scoped `--run --reconcile <original-attempt-folder>` requalifies the preserved first stand-in assertion failure without starting a new Exchange: it verifies the saved run/history against actual completed rows, unchanged source data, no surviving process and no unrelated target additions. SQL timestamp columns compare as instants across display offsets; saved text and JSON are never normalized by that comparison.

The intentional fault holds a row-preserving source-table lock, observes the source COPY blocked by that exact owned backend, verifies the migration command's direct `psql` child and private copy directory, and freezes only its anchored PID/start identity. Nested guards thaw that client and restore the unchanged service on failures and catchable interruption; the failed command must remove its copy folder. Snapshot hashes use deterministic server-encoded rows in one UTC `REPEATABLE READ READ ONLY` transaction. No installed migration SQL is modified. Each durable phase refuses replay after qualification; creation refuses existing Jensen state/settings, and migration refuses a working Jensen. Earlier Sapling-only operational drills require Sapling to be current and refuse once Jensen is current; their qualified receipts remain valid. No operational phase runs during automatic Build checks.
