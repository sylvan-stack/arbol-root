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

# TEST-TIER-DISABLED-BEGIN tests/test_listing_form.py::ListingForm.test_published_listing_fields_and_meanings_are_kept_with_only_additions
#     def test_published_listing_fields_and_meanings_are_kept_with_only_additions(self) -> None:
#         """root.list-form"""
#         expected = json.loads((ROOT / 'tests/fixtures/listing-v1.json').read_text())
#         with tempfile.TemporaryDirectory(prefix='rtm-form-') as temp:
#             base = Path(temp)
#             value = record(1)
#             folder = base / 'exchanges' / str(value['exchange'])
#             folder.mkdir(parents=True)
#             (folder / 'record.json').write_text(json.dumps(value))
#             context = Identity('sapling','7','1.0.0',base,base / 'no-launcher')
#             with mock.patch('arbol_root.process.started_at',return_value=datetime(2026,10,26,9,tzinfo=UTC)):
#                 self.additions_only(expected,listing(context))
# TEST-TIER-DISABLED-END tests/test_listing_form.py::ListingForm.test_published_listing_fields_and_meanings_are_kept_with_only_additions

# Archived complete imports; restore needed names in their original scope, not at this file tail.
# TEST-TIER-IMPORTS-BEGIN tests/test_listing_form.py:3
# import json
# TEST-TIER-IMPORTS-END tests/test_listing_form.py:3
# TEST-TIER-IMPORTS-BEGIN tests/test_listing_form.py:5
# import tempfile
# TEST-TIER-IMPORTS-END tests/test_listing_form.py:5
# TEST-TIER-IMPORTS-BEGIN tests/test_listing_form.py:7
# from datetime import UTC, datetime
# TEST-TIER-IMPORTS-END tests/test_listing_form.py:7
# TEST-TIER-IMPORTS-BEGIN tests/test_listing_form.py:9
# from unittest import mock
# TEST-TIER-IMPORTS-END tests/test_listing_form.py:9
# TEST-TIER-IMPORTS-BEGIN tests/test_listing_form.py:11
# from test_listing import record
# TEST-TIER-IMPORTS-END tests/test_listing_form.py:11
# TEST-TIER-IMPORTS-BEGIN tests/test_listing_form.py:14
# from arbol_root.listing import listing  # noqa: E402
# TEST-TIER-IMPORTS-END tests/test_listing_form.py:14
# TEST-TIER-IMPORTS-BEGIN tests/test_listing_form.py:15
# from arbol_root.model import Identity  # noqa: E402
# TEST-TIER-IMPORTS-END tests/test_listing_form.py:15
