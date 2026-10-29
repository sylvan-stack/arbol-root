# Tests: arbol-root

Both tiers have uncommented source. Only the top-tier cases below may be selected during implementation. They may be selected when useful during implementation; running tests after every change is not required. Writing or running mid-tier tests requires a separate testing task explicitly requested by the owner. Do not write or restore low-tier tests.

[Mid-tier descriptions and justifications](MID_TIER.md) · [Complete inventory and tier justifications](docs/test-inventory.md) · [Machine-readable inventory](test-tiers.json)

Reviewed revision: `c5a544ec3a254ad64588a0cb7940f65b2ae26455` (28 October 2026), plus the preceding local pruning changes. No tests were run for this reset.

## Selection and limits

3 top-tier inventory entries and 267 mid-tier entries are available. Definitions, scenarios, programs and entry points overlap; this is not a runtime suite count. Mid-tier source remains uncommented at the owner's request. Provisional classifications are execution decisions, not semantic approval. Low-tier removals remain removed.

## Active top tier

| Exact selector or program | Why this case earns a place |
| --- | --- |
| [`test_top_groups.GroupIdentity.test_reused_or_unanchored_group_is_never_killed_after_term`](tests/top/test_top_groups.py#L18) | Changes the process table between TERM and escalation. Requires refusal without a second signal when the leader is reused or no previously verified member remains. |
| [`test_top_start.Starting.test_returns_on_a_fragmented_object_without_waiting_for_trunk_exit`](tests/top/test_top_start.py#L14) | Splits an acceptance JSON object across writes after diagnostic/non-object output, while the Trunk stays alive. Requires an immediate valid reply instead of waiting for process exit or rejecting a partial frame. |
| [`test_top_start.Starting.test_timeout_keeps_request_and_process_and_a_late_writer_can_still_finish`](tests/top/test_top_start.py#L24) | Holds the reply beyond the start timeout. Confirms the request bytes and child survive the uncertain outcome and the child can subsequently finish, preventing destructive timeout cleanup. |

## Layout and shared support

Case bodies are separated into [`tests/top/`](tests/top/) and [`tests/mid/`](tests/mid/). The former mixed test modules retain shared fixture classes, helper functions and imports at their established paths, with no inventoried test methods. This preserves existing subprocess paths, patch targets and fixture imports without copying helpers into both tiers. Compatibility entries preserve original package and resource paths while loading the mid-tier implementation. Product-side test APIs load it only when invoked and refuse if the test source is absent.

## Running a selected top-tier case

Select an exact method when it resolves a concrete uncertainty; no run is required after an edit. The new module names begin with test_top_ so they cannot shadow the shared fixture modules. Do not run whole folders or discovery as a substitute. Original prerequisites, skips and environment limitations still apply. A focused result is not full qualification.

From the repository root, using the prepared repository interpreter:

```sh
PYTHONPATH=src:tests:tests/top python -m unittest test_top_groups.GroupIdentity.test_reused_or_unanchored_group_is_never_killed_after_term
```

## Mid-tier execution

[MID_TIER.md](MID_TIER.md) lists the descriptions, tier reasons and review status. The source is now uncommented and stays that way. Writing or running it still requires a separately requested testing task. Do not run tests automatically after edits or merges. Inspect prerequisites and indirect calls before invoking a program or qualification entry point. A focused result is not full qualification.

For a Python method, use the same fixture setup as the top tier, put the mid folder on PYTHONPATH, and select `test_mid_<module>.Class.test_method`. Mycel's fixture-aware runner accepts `--tests tests/mid --select test_mid_<module>.Class.test_method`; store cases require explicit disposable-store settings. Archived scenarios and programs retain their original compatibility entry paths.

Restoration under SYL-326 used static checks only. No tests, Builds, provider calls, Origin migrations or corpus ingest were performed. Original prerequisites and environment limits still apply.
