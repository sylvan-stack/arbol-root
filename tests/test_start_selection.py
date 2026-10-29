# Shared fixtures; case bodies live in top/ and mid/. See TESTS.md.
from __future__ import annotations
import copy
from unittest import mock


import sys
import unittest
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))
from arbol_root.input import FORWARD, parse  # noqa: E402
from arbol_root.launcher import Reply, select_build  # noqa: E402
from arbol_root.model import Identity, Refusal  # noqa: E402

from arbol_root.model import Identity  # noqa: E402

EXCHANGE = '7f3a2c1e-4b5d-4e6f-8a9b-0c1d2e3f4a5b'
BASE = ['start','--exchange',EXCHANGE,'--request','request.json']
INVENTORY: dict[str, Any] = {'root':'sapling','rootContract':1,'trunks':[{'trunk':'trivial','builds':[
    {'build':'a','status':'working','fits':True,'runnable':True,'chosen':True},
    {'build':'9','status':'withdrawn','fits':True,'runnable':True,'chosen':False},
    {'build':'8','status':'working','fits':False,'runnable':True,'chosen':False}]}]}


class Selection(unittest.TestCase):
    context = Identity('sapling','0','1.0.0',Path('/private-fixture/root'),Path('/private-fixture/bin'))


# Archived complete imports; restore needed names in their original scope, not at this file tail.

# LOW TIER — DO NOT ENABLE OR RECREATE
# Historical examples only. Read before adding related tests; never execute.
# LOW-TIER-BEGIN: tests/test_start_selection.py::Selection.test_explicit_build_does_not_query_the_launcher
# Reason: Mocks list_reply around a direct explicit-build return already exercised in the real start path.
# Source: arbol-root@c22615cdb94b4ba89eb56267d1712d38d6254d98:tests/test_start_selection.py
# Retained evidence at review: Starting.test_explicit_build_skips_list_and_does_not_read_a_fifo_request.
# Historical fixtures and class context are available at the source revision; no active dependencies restored.
# LOW-TIER-SOURCE-BEGIN
#     def test_explicit_build_does_not_query_the_launcher(self) -> None:
#         """root.start-named"""
#         with mock.patch('arbol_root.launcher.list_reply') as query:
#             self.assertEqual(select_build(self.context, parse([*BASE,'-v','b'])), 'b')
#         query.assert_not_called()
# LOW-TIER-SOURCE-END
# LOW-TIER-END

# LOW-TIER-BEGIN: tests/test_start_selection.py::Selection.test_uses_the_chosen_build_from_exact_root_and_trunk_inventory
# Reason: Supplies one pre-marked chosen build and checks its name plus mocked call arguments.
# Source: arbol-root@c22615cdb94b4ba89eb56267d1712d38d6254d98:tests/test_start_selection.py
# Retained evidence at review: Actual start/build selection integration and malformed or ambiguous inventory/no-fit cases remain.
# Historical fixtures and class context are available at the source revision; no active dependencies restored.
# LOW-TIER-SOURCE-BEGIN
#     def test_uses_the_chosen_build_from_exact_root_and_trunk_inventory(self) -> None:
#         """root.start-chosen"""
#         with mock.patch('arbol_root.launcher.list_reply', return_value=Reply(b'{}',copy.deepcopy(INVENTORY),0)) as query:
#             self.assertEqual(select_build(self.context, parse(BASE)), 'a')
#         query.assert_called_once_with('sapling',['trivial'],self.context.bin_dir)
# LOW-TIER-SOURCE-END
# LOW-TIER-END

# LOW-TIER-BEGIN: tests/test_start_selection.py::Selection.test_launcher_refusal_is_the_same_raw_reply
# Reason: Asserts object identity for the direct error-return branch after supplying the mock reply.
# Source: arbol-root@c22615cdb94b4ba89eb56267d1712d38d6254d98:tests/test_start_selection.py
# Retained evidence at review: Starting.test_refusal_line_is_unchanged_and_also_removes_request checks the actual public refusal and cleanup.
# Historical fixtures and class context are available at the source revision; no active dependencies restored.
# LOW-TIER-SOURCE-BEGIN
#     def test_launcher_refusal_is_the_same_raw_reply(self) -> None:
#         """root.start-selection-refusal"""
#         reply = Reply(b' {"error":{"code":"unknown_trunk"},"available":[]}\n', {'error':{'code':'unknown_trunk'}},1)
#         with mock.patch('arbol_root.launcher.list_reply', return_value=reply):
#             self.assertIs(select_build(self.context, parse(BASE)), reply)
# LOW-TIER-SOURCE-END
# LOW-TIER-END
