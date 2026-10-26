"""The scenarios of RCT-4, in the order of its table.

A scenario without `run` is not implemented yet: each comes with the Trivial Trunk task that makes it pass, and
RCT-4.3 closes with the last of them (SYL-178). A whole run of the suite reports every scenario that is not
implemented yet as failed, so that no Trunk Build passes against half a suite; `--only` refuses to choose one. R16 is
no scenario of its own: it runs after every scenario (runner.py).
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

from .home import ScenarioHome
from .scenarios import r1, r2, r3, r4, r5, r8, r9, r10, r19


@dataclass(frozen=True)
class Scenario:
    id: str
    title: str
    covers: tuple[str, ...]
    run: Callable[[ScenarioHome], None] | None = None


AFTER_EVERY_SCENARIO = "R16"

SCENARIOS: list[Scenario] = [
    Scenario("R1", "A plain answer in the background",
             ("RCT-0.4", "0.6", "0.14", "1.1", "1.2", "1.5", "2.1", "2.4", "2.9", "2.20", "3.1", "3.2", "3.3"), r1.run),
    Scenario("R2", "The foreground, a failed and a cancelled one, Ctrl-C, and an output nothing reads",
             ("RCT-2.5", "2.8", "2.19"), r2.run),
    Scenario("R3", "Refusals", ("RCT-0.3", "0.5", "2.2", "2.13", "2.17"), r3.run),
    Scenario("R4", "A repeat", ("RCT-2.3", "2.18", "2.19"), r4.run),
    Scenario("R5", "A chat goes on", ("RCT-0.4", "0.5", "2.17"), r5.run),
    Scenario("R6", "Signs of life", ("RCT-1.3",)),
    Scenario("R7", "A Trunk that hangs", ("RCT-1.4", "2.6", "2.12")),
    Scenario("R8", "Stop", ("RCT-1.7", "2.7"), r8.run),
    Scenario("R9", "An answer to a question", ("RCT-1.7", "1.11"), r9.run),
    Scenario("R10", "The termination signal in the middle of a run", ("RCT-2.8", "2.12"), r10.run),
    Scenario("R11", "Failures", ("RCT-2.9", "2.10", "2.20")),
    Scenario("R12", "The database away", ("RCT-2.11", "2.12")),
    Scenario("R13", "Settling at its edges", ("RCT-1.9", "2.12", "3.4")),
    Scenario("R14", "Sending again", ("RCT-2.13", "3.4", "3.9")),
    Scenario("R15", "Size limits", ("RCT-1.6", "1.12")),
    Scenario("R17", "Characters PostgreSQL cannot store", ("RCT-3.10",)),
    Scenario("R18", "A Driver that falls silent", ("RCT-2.21",)),
    Scenario("R19", "Small calls", ("RCT-1.11", "2.22"), r19.run),
]


def select(only: str | None, available: list[Scenario] | None = None) -> list[Scenario]:
    """The scenarios `--only` names, comma- or space-separated, in the order of the registry; all without it."""
    available = SCENARIOS if available is None else available
    if only is None:
        return list(available)
    ids = [item for item in only.replace(",", " ").split() if item]
    if not ids:
        raise ValueError("Give --only at least one scenario, such as --only R1,R8.")
    by_id = {scenario.id: scenario for scenario in available}
    for scenario_id in ids:
        if scenario_id == AFTER_EVERY_SCENARIO:
            raise ValueError("R16 runs after every scenario and cannot be chosen alone.")
        if scenario_id not in by_id:
            raise ValueError(f"Unknown scenario: {scenario_id}. Scenarios: {', '.join(by_id)}.")
    for scenario_id in ids:
        if by_id[scenario_id].run is None:
            raise ValueError(f"Scenario {scenario_id} is not implemented yet.")
    return [scenario for scenario in available if scenario.id in ids]
