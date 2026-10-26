"""Compare the scenario registry with the independently sourced requirement index."""

import unittest

from rct_conformance.registry import SCENARIOS
from rct_conformance.requirements import CONFORMANCE_REQUIREMENTS


class Coverage(unittest.TestCase):
    def test_every_trunk_requirement_naming_contract_has_a_scenario(self) -> None:
        covered = {ref if ref.startswith("RCT-") else "RCT-" + ref
                   for scenario in SCENARIOS for ref in scenario.covers}
        missing = CONFORMANCE_REQUIREMENTS - covered
        self.assertEqual(missing, set(), "No scenario covers: " + ", ".join(sorted(missing)))
