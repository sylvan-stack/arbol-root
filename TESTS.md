# Tests: arbol-root

All test work, including top-tier cases, requires a separate task explicitly requested by the owner. Implement and polish code first; only the owner decides when it is ready for tests. Do not write, edit, maintain or run tests during implementation. Keep existing source in its documented state and low-tier examples commented at file ends.

[Mid-tier descriptions and justifications](MID_TIER.md) · [Complete inventory and tier justifications](docs/test-inventory.md) · [Machine-readable inventory](test-tiers.json)

Reviewed revision: `ef4fd6a30eca7130653b20e5eedf0da7be72aaa4` under SYL-327 (29 October 2026). No tests were run.

## Selection and limits

3 top-tier inventory entries and 52 mid-tier entries are available after the higher-bar review. 215 low-tier entries were removed under SYL-327. Definitions, scenarios, programs and entry points overlap; this is not a runtime suite count. Top-tier bodies are unchanged. Retained mid-tier sources remain uncommented.

## Active top tier

| Exact selector or program | Why this case earns a place |
| --- | --- |
| [`test_top_groups.GroupIdentity.test_reused_or_unanchored_group_is_never_killed_after_term`](tests/top/test_top_groups.py#L18) | Changes the process table between TERM and escalation. Requires refusal without a second signal when the leader is reused or no previously verified member remains. |
| [`test_top_start.Starting.test_returns_on_a_fragmented_object_without_waiting_for_trunk_exit`](tests/top/test_top_start.py#L14) | Splits an acceptance JSON object across writes after diagnostic/non-object output, while the Trunk stays alive. Requires an immediate valid reply instead of waiting for process exit or rejecting a partial frame. |
| [`test_top_start.Starting.test_timeout_keeps_request_and_process_and_a_late_writer_can_still_finish`](tests/top/test_top_start.py#L24) | Holds the reply beyond the start timeout. Confirms the request bytes and child survive the uncertain outcome and the child can subsequently finish, preventing destructive timeout cleanup. |

## Layout and shared support

Case bodies are separated into [`tests/top/`](tests/top/) and [`tests/mid/`](tests/mid/). The former mixed test modules retain shared fixture classes, helper functions and imports at their established paths, with no inventoried test methods. This preserves existing subprocess paths, patch targets and fixture imports without copying helpers into both tiers. Compatibility entries preserve original package and resource paths while loading the mid-tier implementation. Product-side test APIs load it only when invoked and refuse if the test source is absent.

## Running a selected top-tier case in an owner-requested testing task

Select an exact method when it resolves a concrete uncertainty; no run is required after an edit. The new module names begin with test_top_ so they cannot shadow the shared fixture modules. Do not run whole folders or discovery as a substitute. Original prerequisites, skips and environment limitations still apply. A focused result is not full qualification.

From the repository root, using the prepared repository interpreter:

```sh
PYTHONPATH=src:tests:tests/top python -m unittest test_top_groups.GroupIdentity.test_reused_or_unanchored_group_is_never_killed_after_term
```

## Mid-tier execution

[MID_TIER.md](MID_TIER.md) lists the descriptions, tier reasons and review status. The source is now uncommented and stays that way. Writing or running it still requires a separately requested testing task. Do not run tests automatically after edits or merges. Inspect prerequisites and indirect calls before invoking a program or qualification entry point. A focused result is not full qualification.

For a Python method, use the same fixture setup as the top tier, put the mid folder on PYTHONPATH, and select `test_mid_<module>.Class.test_method`. Mycel's fixture-aware runner accepts `--tests tests/mid --select test_mid_<module>.Class.test_method`; store cases require explicit disposable-store settings. Archived scenarios and programs retain their original compatibility entry paths.

Restoration under SYL-326 used static checks only. No tests, Builds, provider calls, Origin migrations or corpus ingest were performed. Original prerequisites and environment limits still apply.

## Qualification after SYL-327

The packaged unit gate no longer stands for the former complete Build qualification: since SYL-329 it runs the top tier only, as Builds below says. Individual top and mid selections remain governed by the policy above; their results cannot stand in for the former complete Build qualification.

## Builds

Since SYL-329 (29 October 2026) a Build runs the top tier only. Its only check, `unit`, runs every case under `tests/top/`. The layout and migration programs and the conformance-suite tests are mid tier, so `arbol-build.json` no longer lists them; run them when the owner asks. The mid tier runs only when the owner asks for a mid-tier run.

## Owner-controlled testing and archived examples — SYL-330

All test work is separate from implementation, including top-tier regressions,
fixtures, snapshots, classification, archival maintenance and runner changes.
Only the owner decides readiness and requests the testing task; do not create
one autonomously or widen implementation into testing. A test-running Build
also belongs to a separately requested testing/Build task; its gate stays intact.
A test review, writing or archival task does not itself authorize execution.

Read the retained cases and the `LOW TIER — DO NOT ENABLE OR RECREATE` footers
before adding related tests. They preserve rejected historical source, reasons
and revisions, so obvious or redundant checks are not generated again. All
archived lines are comments, including imports and registrations. They add no
runnable coverage. Re-admission needs distinct new evidence and owner-requested
test work; a testing request alone does not make low-tier cases useful.
