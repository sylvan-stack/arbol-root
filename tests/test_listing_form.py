# Shared fixtures only; test bodies are in top/ and mid/. See TESTS.md.
from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))

ROOT = Path(__file__).resolve().parents[1]


class ListingForm(unittest.TestCase):
    def additions_only(self, expected: object, actual: object) -> None:
        self.assertIs(type(actual), type(expected))
        if isinstance(expected, dict):
            assert isinstance(actual, dict)
            for key,value in expected.items():
                self.assertIn(key, actual)
                self.additions_only(value,actual[key])
        elif isinstance(expected, list):
            assert isinstance(actual, list)
            self.assertEqual(len(expected), len(actual))
            for before,after in zip(expected,actual,strict=True):
                self.additions_only(before,after)
        else:
            self.assertEqual(expected, actual)


# Archived complete imports; restore needed names in their original scope, not at this file tail.
