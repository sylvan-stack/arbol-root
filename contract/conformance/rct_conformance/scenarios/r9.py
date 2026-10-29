# Test implementations moved to tests/mid/archived/contract/conformance/rct_conformance/scenarios/r9.py.
"""R9: an answer to a question (RCT-4).

The stand-in asks the Leather Bag a question, and the suite appends an answer line to `control`, with its fields in an
order of its own. The suite judges: the stand-in got the answer line unchanged, and the run went on; the answer is a
line of `events.jsonl`, exactly as it was in `control`, between the question's `ask_opened` and `ask_closed`; and the
question's row holds the question and the answer.

Covers RCT-1.7 and 1.11.
"""

from __future__ import annotations

from ..home import ScenarioHome

MESSAGE = "Push the branch."
CHOSEN = {"type": "answers", "answers": {"branch": ["main"]}}


def run(home: ScenarioHome) -> None:
    raise RuntimeError('Tests are commented under the tier policy; see TESTS.md. Restore only in an explicitly requested testing task.')  # TEST-TIER-REFUSAL

# Archived complete imports; restore needed names in their original scope, not at this file tail.
