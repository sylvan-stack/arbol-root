"""Running the scenarios, each in a home of its own, with R16 after each, and reporting them (RCT-4)."""

from __future__ import annotations

from collections.abc import Callable

from .home import ScenarioHome
from .judge import Mismatch, describe
from .registry import Scenario

MakeHome = Callable[[Scenario], ScenarioHome]


def run_suite(selected: list[Scenario], make_home: MakeHome, write: Callable[[str], None]) -> int:
    """Runs the scenarios one after another and writes one line for each: 0 when every one passed, else 1."""
    passed = 0
    for scenario in selected:
        heading = f"{scenario.id} — {scenario.title}"
        if scenario.run is None:
            write(f"FAIL {heading}")
            write("  Not implemented yet.")
            continue
        home: ScenarioHome | None = None
        failure: BaseException | None = None
        stderr = ""
        try:
            home = make_home(scenario)
            scenario.run(home)
            home.no_table_changed()  # R16
        except Exception as error:
            failure = error
            stderr = home.stderr() if home is not None else ""
        finally:
            if home is not None:
                try:
                    home.close()
                except Exception as error:
                    failure = failure or error
        if failure is None:
            write(f"PASS {heading}")
            passed += 1
            continue
        write(f"FAIL {heading}")
        write(f"  {type(failure).__name__ if not str(failure) else str(failure)}")
        if isinstance(failure, Mismatch) and (failure.expected is not None or failure.actual is not None):
            write(f"  Expected: {describe(failure.expected)}")
            write(f"  Received: {describe(failure.actual)}")
        if stderr:
            write("  The Trunk's standard error:\n    " + stderr.replace("\n", "\n    "))
    write(f"{passed}/{len(selected)} scenarios passed.")
    return 0 if passed == len(selected) else 1
