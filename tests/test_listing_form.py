from __future__ import annotations

import json
import sys
import tempfile
import unittest
from datetime import UTC, datetime
from pathlib import Path
from unittest import mock

from test_listing import record

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))
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

    def test_published_listing_fields_and_meanings_are_kept_with_only_additions(self) -> None:
        """root.list-form"""
        expected = json.loads((ROOT / 'tests/fixtures/listing-v1.json').read_text())
        with tempfile.TemporaryDirectory(prefix='rtm-form-') as temp:
            base = Path(temp)
            value = record(1)
            folder = base / 'exchanges' / str(value['exchange'])
            folder.mkdir(parents=True)
            (folder / 'record.json').write_text(json.dumps(value))
            context = Identity('sapling','7','1.0.0',base,base / 'no-launcher')
            with mock.patch('arbol_root.process.started_at',return_value=datetime(2026,10,26,9,tzinfo=UTC)):
                self.additions_only(expected,listing(context))

    def test_two_root_listings_combine_by_their_exchange_entries(self) -> None:
        """root.list-combined"""
        with tempfile.TemporaryDirectory(prefix='rtm-combined-') as temp:
            base = Path(temp)
            results = []
            for number,name in enumerate(['sapling','second'],1):
                value = record(number,root=name)
                root = base / name
                folder = root / 'exchanges' / str(value['exchange'])
                folder.mkdir(parents=True)
                (folder / 'record.json').write_text(json.dumps(value))
                context = Identity(name,str(number),'1.0.0',root,base / 'no-launcher')
                with mock.patch('arbol_root.process.started_at',return_value=None):
                    results.append(listing(context))
            combined = [item for result in results for item in result['exchanges']]
            self.assertEqual([item['root'] for item in combined], ['sapling','second'])
            self.assertEqual([item['state'] for item in combined], ['interrupted','interrupted'])
            self.assertEqual([result['rootBuild'] for result in results], ['1','2'])
