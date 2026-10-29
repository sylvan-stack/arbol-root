"""Commented mid-tier selections; see MID_TIER.md before restoring a case."""

# Restore the needed imports and class header only for an explicit testing task.
# import test_listing_form as _support
# from test_listing_form import (
#     ListingForm,
#     Path,
#     ROOT,
#     sys,
#     unittest,
# )


# class ListingForm(_support.ListingForm):
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


# Original deferred imports (restore at the required scope, never blindly at the tail).
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

raise RuntimeError("Mid-tier tests require an explicitly requested testing task; see MID_TIER.md.")
