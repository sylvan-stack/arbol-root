# Shared fixtures; case bodies live in top/ and mid/. See TESTS.md.
from __future__ import annotations
import json
import tempfile
from datetime import UTC, datetime
from unittest import mock


import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))
from test_listing import record
from arbol_root.listing import listing  # noqa: E402
from arbol_root.model import Identity  # noqa: E402


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

# LOW TIER — DO NOT ENABLE OR RECREATE
# Historical examples only. Read before adding related tests; never execute.
# LOW-TIER-BEGIN: tests/test_listing_form.py::ListingForm.test_two_root_listings_combine_by_their_exchange_entries
# Reason: The test itself concatenates two independent listings, then checks ordinary root labels; it exercises no product aggregation behavior.
# Source: arbol-root@9acb69d393aed7dcdea8a7d74711f880340983d0:tests/test_listing_form.py
# Retained evidence at review: Published listing compatibility and state/partial-failure listing cases remain.
# Historical fixtures and class context are available at the source revision; no active dependencies restored.
# LOW-TIER-SOURCE-BEGIN
#     def test_two_root_listings_combine_by_their_exchange_entries(self) -> None:
#         """root.list-combined"""
#         with tempfile.TemporaryDirectory(prefix='rtm-combined-') as temp:
#             base = Path(temp)
#             results = []
#             for number,name in enumerate(['sapling','second'],1):
#                 value = record(number,root=name)
#                 root = base / name
#                 folder = root / 'exchanges' / str(value['exchange'])
#                 folder.mkdir(parents=True)
#                 (folder / 'record.json').write_text(json.dumps(value))
#                 context = Identity(name,str(number),'1.0.0',root,base / 'no-launcher')
#                 with mock.patch('arbol_root.process.started_at',return_value=None):
#                     results.append(listing(context))
#             combined = [item for result in results for item in result['exchanges']]
#             self.assertEqual([item['root'] for item in combined], ['sapling','second'])
#             self.assertEqual([item['state'] for item in combined], ['interrupted','interrupted'])
#             self.assertEqual([result['rootBuild'] for result in results], ['1','2'])
# LOW-TIER-SOURCE-END
# LOW-TIER-END
