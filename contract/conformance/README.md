# Root Contract conformance

One program checks a Trunk Build against the Root Contract ([RCT-4](https://github.com/sylvan-stack/arbol-root-artifacts/blob/main/contract/04-conformance.md)). It starts the Build's own program as `arbol-root` and a person would, in a home folder of its own with a Root record for the test, a stand-in that plays a Driver from a script, and a PostgreSQL server of its own with a database made from `contract/<version>/layout.sql`. It judges only what the Trunk prints, its exit status, the Exchange folder, the tables read with `psql`, and what the stand-in received. It needs no network, no account and no quota.

The suite is typed Python on Python 3.14 that uses only the standard library. It needs PostgreSQL's programs `initdb`, `pg_ctl`, `createdb` and `psql` on the search path; without them it ends with 2 and names the missing ones. From the repository's folder:

```sh
python3.14 contract/conformance/bin/rct-conformance.py --trunk "$ARBOL_BUILD_DIR/bin/arbol-trunk-trivial" --root-contract 1
python3.14 contract/conformance/bin/rct-conformance.py --trunk "…" --root-contract 1 --only R3,R8
```

`--trunk` is what starts the Trunk Build's own program, not the launcher: a path, or a name found on the search path, with any fixed arguments in the same quoted value, such as `--trunk 'python3.14 trunks/trivial/src/main.py'`. The suite adds `--root rct` and the command. The exit status is 0 when every scenario passed, 1 when one failed, and 2 for wrong input, for PostgreSQL's programs missing, or when the suite was stopped.

## What each scenario gets

`rct_conformance/home.py` makes, for every scenario, and removes again afterwards:

- a new temporary folder as the Trunk's home;
- a server made with `initdb` in it, trusting the role `rct`, listening only on a socket in a short folder under `/tmp` (`rct_conformance/postgres.py`);
- the Root record `<home>/Library/Application Support/Arbol/roots/rct/root.json`, with `rootContract` set to the version under test and `"database": "arbol_rct"`, and an empty `exchanges/` of the mode 0700;
- the database `arbol_rct`, made with `createdb`, with the version's `layout.sql` run by `psql`;
- `<home>/.arbol/database.json` with the socket's address, such as `postgresql://rct@%2Ftmp%2Frct-1a2b`;
- the stand-in Driver `standin/driver.py`, first on the search path as `arbol-claude-driver` and `arbol-codex-driver`.

The Trunk gets only `HOME`, `PATH` (the stand-in's folder, then `/usr/bin:/bin:/usr/sbin:/sbin`), `LANG` and the test's own variables: `ARBOL_TEST_TIME_SCALE=10` unless a scenario says otherwise, and `ARBOL_TEST_HANG=1` where a scenario asks for it. No `PG…` variable of the owner's shell reaches the Trunk or the suite's own calls of PostgreSQL's programs, so no scenario can reach the installed server or a Root in use.

After every scenario, R16 compares PostgreSQL's catalogue of the database with the one read right after `layout.sql` made it, and checks that every row belongs to an Exchange that one of the scenario's acceptance lines named.

## Writing a scenario

Each scenario comes with the Trivial Trunk task that makes it pass. To add one:

1. Write `run(home: ScenarioHome) -> None` in `rct_conformance/scenarios/r<number>.py`, such as `r1.py`, and give it to the scenario's entry in `rct_conformance/registry.py`. A scenario without `run` is not implemented yet: a whole run reports it as failed, and `--only` refuses it.
2. Judge with what `ScenarioHome` offers, and nothing else:
   - `home.part("tool")` names the script the stand-in plays from now on, "R8 tool"; `home.release()` lets the runs it holds open (`hold()`) go on, until the next part is named;
   - `home.start(message, …)` starts `run --detach` as `arbol-root` does: `--exchange <id> --request <file>`, the request naming the Driver, the Subscription and the model, in a process group and session of its own, with standard input from `/dev/null`; it reads one line and gives it with the Trunk's process and how long the answer took; `root=` names another Root identifier than `rct`, and `meanwhile=` a function that runs once the Trunk is started and before its line is read; starts may run from several threads at once, such as two messages to one chat at the same moment;
   - `home.acceptances_held()` holds every acceptance, with a lock on `chats` that lets the tables be read and no row be written, until its `release()` or the end of its `with` block, such as for a line written to `control` while the Trunk accepts;
   - `home.run(args)` runs a command to its end, such as `settle <exchange>` or `run` in the foreground; `home.spawn(args)` starts one and leaves its output to the scenario;
   - `home.folders()`, `home.record(exchange)`, `home.events(exchange)` and `home.control(exchange, line)` read and write the Exchange folder as a reader and a writer of `control` do; `home.follow(exchange)` keeps `events.jsonl` open, so that its lines can be read after the Trunk has removed the folder;
   - `home.rows(query)` reads the tables with `psql`; `home.server.stop()` and `home.server.start()` take the database away and bring it back;
   - `home.received()` gives the stand-in's records, each with the lines it wrote as `events` (RCT-D33), and `home.children()` the children it started;
   - `check`, `equal` and `wait_until` of `rct_conformance/judge.py` report what was expected and what was found.
3. Add the scenario's scripts to `SCRIPTS` in `standin/driver.py`, under "<scenario> <part>" or "<scenario>". A script is a function of a `Run`: `started()`, `text()`, `tool()`, `shell()`, `open_tool()`, `ask()`, `usage()`, `silence(seconds)` (divided by the time scale), `hold()` (until the suite's `home.release()`), `child()`, `wait_for_stop()` and `finished(outcome)`. A stop line, the end of the control input, SIGTERM, SIGINT and `runs stop` stop a run as a Driver does. A run with `"tools": "none"` and no chat session plays "<scenario> <part> small", else "<scenario> small", else the title "Stand-in title".
4. Name the scenario's check in the requirement tables of RCT-0 to RCT-3.

## The suite's own tests

```sh
uv sync
uv run --no-sync python -B -m unittest discover -s contract/conformance/tests -t contract/conformance
uv run --no-sync ruff check .
uv run --no-sync mypy
```

`tests/test_layout.py` runs `layout.sql` twice on a server of the test's own and checks its comments and refusals; `tests/test_setup.py` the setup of a scenario, the starter, R16 and what closing leaves behind, with a fake Trunk (`tests/fake_trunk.py`); `tests/test_standin.py` the stand-in Driver; `tests/test_cli.py` the command line and the runner.
