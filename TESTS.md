# Tests: arbol-root

Only the top-tier cases below are active. They may be selected when useful during implementation; running tests after every change is not required. Writing, restoring or running mid-tier tests requires a separate testing task explicitly requested by the owner. Do not write or restore low-tier tests.

[Complete inventory and tier justifications](docs/test-inventory.md) · [Machine-readable inventory](test-tiers.json)

Reviewed revision: `c5a544ec3a254ad64588a0cb7940f65b2ae26455` (28 October 2026), plus the preceding local pruning changes. No tests were run for this reset.

## Selection and limits

3 active Python definitions and 0 active standalone programs; 238 commented Python definitions. Also disabled: 0 named Node cases, 18 custom scenario functions and 2 standalone check programs. 9 broad entry points explicitly refuse. 11 low-tier cases remain removed from the prior review. These categories overlap in execution and must not be added into a runtime suite size.

Top-tier cases were individually read for the failure they observe. The remaining mid-tier labels are provisional execution decisions, not a claim that thousands of tests have passed a complete semantic review. Reassess value before restoring any of them. A browser program may contain many assertions; it is inventoried as one indivisible program, not as one asserted behavior.

## Active top tier

| Exact test selector | Why this case earns a place |
| --- | --- |
| [`test_groups.GroupIdentity.test_reused_or_unanchored_group_is_never_killed_after_term`](tests/test_groups.py#L91) | Changes the process table between TERM and escalation. Requires refusal without a second signal when the leader is reused or no previously verified member remains. |
| [`test_start.Starting.test_returns_on_a_fragmented_object_without_waiting_for_trunk_exit`](tests/test_start.py#L118) | Splits an acceptance JSON object across writes after diagnostic/non-object output, while the Trunk stays alive. Requires an immediate valid reply instead of waiting for process exit or rejecting a partial frame. |
| [`test_start.Starting.test_timeout_keeps_request_and_process_and_a_late_writer_can_still_finish`](tests/test_start.py#L128) | Holds the reply beyond the start timeout. Confirms the request bytes and child survive the uncertain outcome and the child can subsequently finish, preventing destructive timeout cleanup. |

## Running a selected top-tier case

Select the exact method, never a whole module as a substitute. Retain the original fixture prerequisites. A missing dependency, skipped case or unavailable database is not a pass. No live-provider check was promoted.

Use the repository interpreter and source/test import paths; for example, from the repository root:

```sh
PYTHONPATH=src:tests python -m unittest test_groups.GroupIdentity.test_reused_or_unanchored_group_is_never_killed_after_term
```

## Restoring a mid-tier selection in an explicit testing task

1. Read the case and its helpers, reassess its information value, and identify the exact requested scope. Delete low-value cases instead of restoring them.
2. Uncomment only the selected `TEST-TIER-DISABLED-BEGIN` / `END` block by removing one leading `# ` (Python) or `// ` (JavaScript) from each original source line. Remove the marker lines. A bare `#` or `//` line inside a block represents an empty original line. Restore needed names from the complete `TEST-TIER-IMPORTS` statements at the file tail into their original scope and normal import section, rather than uncommenting them at the tail. Do not discard other local changes.
3. For standalone programs or custom scenario functions, remove only their adjacent `TEST-TIER-REFUSAL` stub or terminal refusal after restoring the actual implementation. Restore required shared helpers. The empty-suite `pass` is harmless and can be removed once a class has a real body.
4. Update both inventories to reflect the selection. Run only the requested scope, record actual results, then return mid-tier code to comments when the task finishes unless the owner asked to retain it active. Promotion to top tier needs a concrete, individually reviewed reason.

Broad build/qualification checks refuse while their implementation is commented. Preserve that refusal until the requested qualification has its necessary tests restored. A top-only run does not satisfy an old full-suite gate. Metadata verification, production validation, fixture helpers, Storybook examples and historical result records are not test passes and remain separate.
