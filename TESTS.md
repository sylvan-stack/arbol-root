# Tests: arbol-root

Only the top-tier cases below are active. They may be selected when useful during implementation; running tests after every change is not required. Writing, restoring or running mid-tier tests requires a separate testing task explicitly requested by the owner. Do not write or restore low-tier tests.

[Mid-tier descriptions and justifications](MID_TIER.md) · [Complete inventory and tier justifications](docs/test-inventory.md) · [Machine-readable inventory](test-tiers.json)

Reviewed revision: `c5a544ec3a254ad64588a0cb7940f65b2ae26455` (28 October 2026), plus the preceding local pruning changes. No tests were run for this reset.

## Selection and limits

3 active Python definitions and 0 active standalone programs; 238 commented Python definitions. Also disabled: 0 named Node cases, 18 custom scenario functions and 2 standalone check programs. 9 broad entry points explicitly refuse. 11 low-tier cases remain removed from the prior review. These categories overlap in execution and must not be added into a runtime suite size.

Top-tier cases were individually read for the failure they observe. The remaining mid-tier labels are provisional execution decisions, not a claim that thousands of tests have passed a complete semantic review. Reassess value before restoring any of them. A browser program may contain many assertions; it is inventoried as one indivisible program, not as one asserted behavior.

## Active top tier

| Exact selector or program | Why this case earns a place |
| --- | --- |
| [`test_top_groups.GroupIdentity.test_reused_or_unanchored_group_is_never_killed_after_term`](tests/top/test_top_groups.py#L18) | Changes the process table between TERM and escalation. Requires refusal without a second signal when the leader is reused or no previously verified member remains. |
| [`test_top_start.Starting.test_returns_on_a_fragmented_object_without_waiting_for_trunk_exit`](tests/top/test_top_start.py#L14) | Splits an acceptance JSON object across writes after diagnostic/non-object output, while the Trunk stays alive. Requires an immediate valid reply instead of waiting for process exit or rejecting a partial frame. |
| [`test_top_start.Starting.test_timeout_keeps_request_and_process_and_a_late_writer_can_still_finish`](tests/top/test_top_start.py#L24) | Holds the reply beyond the start timeout. Confirms the request bytes and child survive the uncertain outcome and the child can subsequently finish, preventing destructive timeout cleanup. |

## Layout and shared support

Case bodies are separated into [`tests/top/`](tests/top/) and [`tests/mid/`](tests/mid/). The former mixed test modules retain shared fixture classes, helper functions and imports at their established paths, with no inventoried test methods. This preserves existing subprocess paths, patch targets and fixture imports without copying helpers into both tiers. Original check entry points retain their refusals.

## Running a selected top-tier case

Select an exact method when it resolves a concrete uncertainty; no run is required after an edit. The new module names begin with test_top_ so they cannot shadow the shared fixture modules. Do not run whole folders or discovery as a substitute. Original prerequisites, skips and environment limitations still apply. A focused result is not full qualification.

From the repository root, using the prepared repository interpreter:

```sh
PYTHONPATH=src:tests:tests/top python -m unittest test_top_groups.GroupIdentity.test_reused_or_unanchored_group_is_never_killed_after_term
```

## Mid-tier review and restoration

[MID_TIER.md](MID_TIER.md) describes every retained mid-tier entry and its existing reason, identifies provisional classifications and explains restoration. Only a separately requested testing task may restore or run these sources. Keep the source in the mid folder; restore only the selected imports, class headers and bodies, update the inventories, and return the source to comments afterward unless the owner says otherwise. Broad entry points continue to refuse; repairing a qualification workflow requires its own explicit testing task.

Layout revision: `f219b7c5d5789f903c2adcb23d023779ee584789`. No tests were run for this reorganization. Previous identifiers and source lines are retained in test-tiers.json. Indexed Origin relocation and ingest remain deferred; moving files supplies no new runtime proof.
