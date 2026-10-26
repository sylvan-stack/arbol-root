# Arbol Root

Arbol Root: a component of Arbol 2.

It holds the Root Contract's chat tables, `contract/1/layout.sql`, and its conformance suite, `contract/conformance/` (see its [README](contract/conformance/README.md)). The Root manager currently provides `trunks`: it forwards the compatible Trunk inventory through the `arbol-trunk` launcher. Its later commands are not implemented yet.

| | |
|---|---|
| Package | `@sylvan-stack/arbol-root` 1.0.0 |
| Artifact corpus | `~/Artifacts/arbol-root` (GitHub `sylvan-stack/arbol-root-artifacts`) |

## Root manager development and Builds

Run `uv sync --locked --group dev` once. `bin/arbol-root --root <root> trunks` runs the development program (Build 0); a packaged program reads its Root from its adjacent Build record. It reads no settings file or database. `--root-dir` requires `--bin-dir`, pointing tests at a private Root and a stand-in launcher.

`arbol-builds build arbol-root --root <root>` packages checksum-pinned standalone CPython 3.14.8, the standard-library manager, its tests and the conformance suite. The final build command reads the Root record under HOME and copies its version's chat layout, its own layout, and a migration script only when it grew from another Root. A missing required file fails the Build. Only `unit` is defined at this stage; layout and migration qualification follow in SYL-184. No Root on this Mac is created by building the program.

The unit check verifies the complete file manifest (excluding mutable Build records/logs/last-start and Python caches), runs both test families with its own interpreter and verifies integrity again. Tests use fictional records, private homes, scripted launchers and, for the unchanged conformance-suite tests, private socket-only PostgreSQL servers. They use no account or vendor request.

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
