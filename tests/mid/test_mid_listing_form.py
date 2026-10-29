"""Mid-tier selections. Write or run only in an explicitly requested testing task."""
from __future__ import annotations

import test_listing_form as _support
from test_listing_form import (
    Identity,
    ListingForm,
    Path,
    ROOT,
    UTC,
    datetime,
    json,
    listing,
    mock,
    record,
    sys,
    tempfile,
    unittest,
)


class ListingForm(_support.ListingForm):
# TEST-TIER-BEGIN tests/test_listing_form.py::ListingForm.test_published_listing_fields_and_meanings_are_kept_with_only_additions
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
# TEST-TIER-END tests/test_listing_form.py::ListingForm.test_published_listing_fields_and_meanings_are_kept_with_only_additions
